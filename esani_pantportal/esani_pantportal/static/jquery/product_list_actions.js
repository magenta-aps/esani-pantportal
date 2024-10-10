// SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
// SPDX-License-Identifier: MPL-2.0

"use strict";

(function () {
    $(document).ready(function () {
        const approveButton = $("#approve_button");
        const rejectButton = $("#reject_button");
        const deleteButton = $("#delete_button");

        const getSelectedRowIds = function () {
            const rowIds = [];
            $('#table tbody tr input[type="checkbox"]:checked').each(function (index, value) {
                rowIds.push(this.value);
            })

            return rowIds
        }

        const getUnapprovedRows = function () {
            const rowIds = [];
            $('#table tbody tr input[type="checkbox"]:checked').each(function (index, value) {
                const $checkbox = $(this)
                const $tr = $checkbox.parents("tr").first()
                const $status = $tr.find(`td.column-status`)
                const status_text = $status.text().toLowerCase()

                if (status_text === "afventer godkendelse" || status_text === "afvist") {
                    rowIds.push(this.value);
                }
            })

            return rowIds
        }

        const updateProducts = function (url, ids, extra) {
            let data = {
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                ids: ids,
            };

            if (extra) {
                data = { ...data, ...extra };
            }

            $.ajax({
                type: "POST",
                url: url,
                data: data,
                success: function (result) {
                    // Update table contents
                    $table.bootstrapTable("refresh");

                    // Update `state` dropdown items (counts have changed)
                    const stateDropdown = $("#id_state");
                    stateDropdown.html("");  // clear current option elements
                    for (const choice of result.state_choices) {
                        const option = $(
                            "<option value=" + choice.value + ">" + choice.label + "</option>"
                        );
                        stateDropdown.append(option);
                    }

                    // Alert user
                    alert(
                        interpolate(
                            ngettext(
                                "Behandlede %(updated)s produkt ud af %(total)s",
                                "Behandlede %(updated)s produkter ud af %(total)s",
                                result.updated,
                            ),
                            // interpolation context
                            {
                                "updated": result.updated,
                                "total": result.total,
                            },
                            true,  // use named interpolation
                        )
                    );
                }
            });
        }

        const confirmAndUpdateSelected = function (url, rowIds, message) {
            if (rowIds.length > 0) {
                // The `interpolate` function is provided by the Django
                // `javascript-catalog` view, which returns a JS file.
                const text = interpolate(
                    message,  // result of `ngettext` call
                    { "num": rowIds.length },  // interpolation context
                    true,  // use named interpolation
                );

                const confirmed = confirm(text);
                if (confirmed) {
                    updateProducts(url, rowIds);
                }
            }
        }

        const onUpdateSelected = function () {
            const unapprovedRowIds = getUnapprovedRows();
            const rowIds = getSelectedRowIds();

            if (unapprovedRowIds.length > 0) {
                approveButton.removeClass("disabled");
            } else {
                approveButton.addClass("disabled");
            }

            if (rowIds.length > 0) {
                deleteButton.removeClass("disabled");
                rejectButton.removeClass("disabled");
            } else {
                deleteButton.addClass("disabled");
                rejectButton.addClass("disabled");
            }
        }

        approveButton.on("click", function () {
            const rowIds = getUnapprovedRows();

            confirmAndUpdateSelected(
                $(this).data("post-url"),
                rowIds,
                // The `ngettext` function is provided by the Django
                // `javascript-catalog` view, which returns a JS file.
                ngettext(
                    "Er du sikker på at du vil godkende %(num)s produkt?",
                    "Er du sikker på at du vil godkende %(num)s produkter?",
                    rowIds.length
                )
            );
        });

        rejectButton.on("click", function () {
            const rowIds = getSelectedRowIds();

            const promptText = interpolate(
                ngettext(
                    "Angiv venligst en afvisnings-besked for %(num)s valgte produkt",
                    "Angiv venligst en afvisnings-besked for %(num)s valgte produkter",
                    rowIds.length,
                ),
                { "num": rowIds.length },  // interpolation context
                true,  // use named interpolation
            );

            const rejectionText = prompt(promptText);

            if ((rowIds.length > 0) && rejectionText) {
                updateProducts(
                    $(this).data("post-url"),
                    rowIds,
                    { "rejection": rejectionText },
                );
            }
        });

        deleteButton.on("click", function () {
            const rowIds = getSelectedRowIds();

            confirmAndUpdateSelected(
                $(this).data("post-url"),
                rowIds,
                // The `ngettext` function is provided by the Django
                // `javascript-catalog` view, which returns a JS file.
                ngettext(
                    "Er du sikker på at du vil slette %(num)s produkt?",
                    "Er du sikker på at du vil slette %(num)s produkter?",
                    rowIds.length,
                )
            );
        });

        // IMPORTANT: 'row-select-event' is a custom event
        // dispatched/triggered by "list_view_table"
        $("#table").on("row-select-event", function (event) {
            onUpdateSelected();
        })
    });
}());
