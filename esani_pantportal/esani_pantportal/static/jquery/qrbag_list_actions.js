// SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
// SPDX-License-Identifier: MPL-2.0

"use strict";

(function () {
    $(document).ready(function () {
        const hideButton = $("#hide_button");
        const unhideButton = $("#unhide_button");
        const removeManualButton = $("#remove_manual_button");

        const getSelectedRowIds = function () {
            const rowIds = [];
            $('#table tbody tr input[type="checkbox"]:checked').each(function (index, value) {
                rowIds.push(this.value);
            })

            return rowIds
        }

        const updateBags = function (url, ids, extra) {
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
                    const statusDropdown = $("#id_status");
                    statusDropdown.html("");  // clear current option elements
                    for (const choice of result.status_choices) {
                        const option = $(
                            "<option value=" + choice.value + ">" + choice.label + "</option>"
                        );
                        statusDropdown.append(option);
                    }

                    // Alert user
                    alert(
                        interpolate(
                            ngettext(
                                "Behandlede %(updated)s pantpose ud af %(total)s",
                                "Behandlede %(updated)s pantposer ud af %(total)s",
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
                    updateBags(url, rowIds);
                }
            }
        }

        const onUpdateSelected = function () {
            const rowIds = getSelectedRowIds();

            if (rowIds.length > 0) {
                hideButton.removeClass("disabled");
                unhideButton.removeClass("disabled");
                removeManualButton.removeClass("disabled");
            } else {
                hideButton.addClass("disabled");
                unhideButton.addClass("disabled");
                removeManualButton.addClass("disabled");
            }
        }

        hideButton.on("click", function (evt) {
            evt.preventDefault();

            const rowIds = getSelectedRowIds();

            const promptText = interpolate(
                ngettext(
                    "Angiv venligst, hvorfor %(num)s valgt pantpose skal skjules",
                    "Angiv venligst, hvorfor %(num)s valgte pantposer skal skjules",
                    rowIds.length,
                ),
                { "num": rowIds.length },  // interpolation context
                true,  // use named interpolation
            );

            const reasonText = prompt(promptText);

            if ((rowIds.length > 0) && reasonText) {
                updateBags(
                    $(this).data("post-url"),
                    rowIds,
                    { "reason": reasonText },
                );
            }
        });

        unhideButton.on("click", function (evt) {
            evt.preventDefault();

            const rowIds = getSelectedRowIds();

            confirmAndUpdateSelected(
                $(this).data("post-url"),
                rowIds,
                ngettext(
                    "Er du sikker på at du vil fjerne skjult-status fra %(num)s pantpose?",
                    "Er du sikker på at du vil fjerne skjult-status fra %(num)s pantposer?",
                    rowIds.length,
                )
            );
        });

        removeManualButton.on("click", function (evt) {
            evt.preventDefault();

            const rowIds = getSelectedRowIds();

            confirmAndUpdateSelected(
                $(this).data("post-url"),
                rowIds,
                ngettext(
                    "Er du sikker på at du vil fjerne manuelt indtastet pant fra %(num)s pantpose?",
                    "Er du sikker på at du vil fjerne manuelt indtastet pant fra %(num)s pantposer?",
                    rowIds.length,
                )
            );
        });

        // IMPORTANT: 'row-select-event' is a custom event dispatched/triggered
        // by "list_view_table".
        $("#table").on("row-select-event", function (event) {
            onUpdateSelected();
        })
    });
}());
