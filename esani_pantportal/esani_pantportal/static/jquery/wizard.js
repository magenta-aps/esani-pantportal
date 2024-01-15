// SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
// SPDX-License-Identifier: MPL-2.0

"use strict";

(function () {
    // Enables "wizard" UI, where the user must complete a set of forms in a series of steps.
    // Each step must be filled out before the next step becomes available.
    // The final step shows a submit button which submits the entire form (= all steps.)
    //
    // This code expects an HTML document with a single form.
    // The form is divided into steps by marking up each steps as a Bootstrap "card".
    // The code below expects to find buttons for "prev", "next" and "submit".

    $(document).ready(function () {
        const prev = $("button#prev");
        const next = $("button#next");
        const submit = $("button#submit");
        const progressBar = $(".progress-bar");
        const totalSteps = $(".card").length;
        let currStep = 1;

        const validateServerSide = function (card) {
            // Validate the visible form fields on the current step by sending it to the
            // server and asking it to validate.

            const visibleFields = $("input:visible, select:visible", card);
            let result = true;
            let formData = visibleFields.serializeArray();
            let prefixes = new Set(
                formData.map(
                    function (field) { return field.name.split("-")[0]; }
                )
            );

            // Add 'prevalidate' field and CSRF token to POST payload
            formData.push(
                {
                    "name": "prevalidate",
                    "value": Array.from(prefixes).join(","),
                },
                {
                    "name": "csrfmiddlewaretoken",
                    "value": $("input[name=csrfmiddlewaretoken]").val(),
                },
            );

            // Validate visible fields server-side
            $.ajax(
                "",
                {
                    method: "POST",
                    async: false,
                    data: formData,
                    success: function (data, status) {
                        // Remove any currently displayed errors
                        $("form .errorlist").remove();

                        for (const prefix of prefixes) {
                            for (const error in data.errors) {
                                const elem = $(`#id_${prefix}-${error}`, card);
                                if ((elem.length !== 0) && (data.errors[error].length !== 0)) {
                                    result = false;

                                    // Add error next to the relevant field
                                    const errorElem = $(`<ul class="errorlist"><li>${data.errors[error][0]}</li></ul>`);
                                    elem.after(errorElem);
                                }
                            }
                        }
                    },
                },
            );

            return result;
        }

        const validateCard = function () {
            // Get currently displayed card
            const card = $(".card:not(.d-none)");

            // Run all validations for card
            return validateServerSide(card);
        }

        const updateNavState = function (overrideCardValid) {
            const displayElem = function (elem, visible) {
                if (visible) {
                    elem.removeClass("d-none");
                } else {
                    elem.addClass("d-none");
                }
            }

            // Determine the states (on or off) for the "next" and "submit" buttons
            const cardValid = overrideCardValid ? true : validateCard();
            const nextVisible = (currStep !== totalSteps);
            const submitVisible = (currStep === totalSteps);

            // Update the DOM state of the buttons
            next.prop("disabled", cardValid ? "" : "disabled");
            displayElem(next, nextVisible);
            displayElem(submit, submitVisible);
        }

        const updateCurrentCard = function (direction) {
            // Get currently displayed card
            const currCard = $(".card:not(.d-none)");

            // Find other (currently invisible cards) - either the following cards, if navigating to the next card,
            // or the preceding cards, if navigating to the previous card.
            const otherCardsSelector = ".card.d-none";
            let otherCard;

            if (direction === "next") {
                otherCard = currCard.next(otherCardsSelector);
            } else {
                otherCard = currCard.prev(otherCardsSelector);
            }


            if (otherCard.length > 0) {
                // Hide the current card, and display the next card
                currCard.addClass("d-none");
                otherCard.removeClass("d-none");
            } else if ((otherCard.length === 0) && (direction === "prev")) {
                // User clicked "prev" button on first card. Take them to the previous URL
                const abortMessage = $("form").data("abort-message");
                if (!!abortMessage && confirm(abortMessage)) {
                    window.history.back();
                }
            }
        }

        const updateProgress = function (newVal) {
            // Clip currStep between 1 and totalSteps
            if (newVal > totalSteps) {
                currStep = totalSteps;
            } else if (newVal < 1) {
                currStep = 1;
            } else {
                currStep = newVal;
            }

            // Update DOM element to reflect new progress (as percentage)
            const widthPercent = Math.round(100 * (currStep / totalSteps));
            progressBar.css("width", widthPercent + "%");
            progressBar.prop("aria-valuenow", widthPercent);
        }

        const gotoFirstCardWithErrors = function () {
            // Determine which card (if any) is the first to contain form errors
            const errorLists = $(".errorlist");
            const invalidFields = $(".is-invalid");
            let elem;
            if (errorLists.length !== 0) {
                elem = errorLists;
            } else if (invalidFields.length !== 0) {
                elem = invalidFields;
            }

            // Display the first card which has an error
            if ((elem !== undefined) && (elem.length !== 0)) {
                const firstCardWithErrors = elem.parents(".card:first");
                if (firstCardWithErrors.length !== 0) {
                    // Update nav state
                    currStep = firstCardWithErrors.index();
                    // Update visibility of cards, so the card with form errors is displayed
                    $(".card").addClass("d-none");
                    firstCardWithErrors.removeClass("d-none");
                }
            }
        }

        // Define behavior for "Next" button
        next.on("click", function (evt) {
            evt.preventDefault();  // Prevent form submit
            updateCurrentCard("next");
            updateProgress(currStep + 1);
            updateNavState();
        });

        // Define behavior for "Previous" button
        prev.on("click", function (evt) {
            evt.preventDefault();  // Prevent form submit
            updateCurrentCard("prev");
            updateProgress(currStep - 1);
            updateNavState();
        });

        // Define behavior for "Submit" button
        submit.on("click", function (evt) {
            // Only allow submitting via "Enter" on final card, and only if card is filled out correctly
            const cardValid = validateCard();
            const canSubmit = cardValid && (currStep === totalSteps);
            if (!canSubmit) {
                evt.preventDefault();
            }
        });

        // Define behavior for form submission
        $("form").on("submit", function (evt) {
            // Disable submit button while form is being POSTed to server, to prevent "double POSTs"
            submit.prop("disabled", "disabled");
        });

        // Define behavior when form elements are changed
        $(".card input, .card select").on("change", function (evt) {
            // When a user edits a field, remove its "error marker", so the "Next" button can become enabled again
            const field = $(evt.target);

            // Also remove "error marker" from hidden CAPTCHA field, if the visible CAPTCHA field is changed
            if (field.attr("id") === "id_user-captcha_1") {
                $("#id_user-captcha_0").removeClass("is-invalid");
            }

            field.removeClass("is-invalid");
            updateNavState();
        });

        // Define behavior of "a#show_<field>" toggles
        $("a[id*='show']").on("click", function (evt) {
            updateNavState();
        });

        // If any form errors are present, go to the first card with form errors
        gotoFirstCardWithErrors();

        // Set up initial state
        updateProgress(currStep);
        updateNavState(true);
    });
}());
