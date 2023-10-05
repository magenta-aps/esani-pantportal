$(function () {
    // Afsender/modtager opdatering
    // ----------------------------
    for (let i = 0; i < aktører.length; i++) {
        const aktør = aktører[i];
        const fields = aktør["fields"];
        const api = aktør["api"];
        for (let j = 0; j < aktør["searchfields"].length; j++) {
            const searchfield = aktør["searchfields"][j];
            fields[searchfield].on("change", function () {
                $.ajax({
                    "url": api + "?" + searchfield + "=" + this.value,
                    "success": function (response_data) {
                        if (response_data["count"] > 0) {
                            const found_item = response_data["items"][0];
                            for (let name in found_item) {
                                if (name in fields) {
                                    fields[name].val(found_item[name]);
                                }
                            }
                        }
                    }
                });
            });
        }
    }
});
$(function () {

    // Vis afgiftssats og beregn afgiftsbeløb
    // --------------------------------------
    const varesatser = JSON.parse($('#varesatser').text());
    const decimal_fields = ["afgiftssats", "segment_nedre", "segment_øvre"];
    for (key in varesatser) {
        const varesats = varesatser[key];
        for (let fieldname of decimal_fields) {
            if (varesats[fieldname]) {
                varesats[fieldname] = parseFloat(varesats[fieldname]);
            }
        }
    }

    const replace_repeat = function (subject, re, replacement) {
        let old = null;
        while (old !== subject) {
            old = subject;
            subject = subject.replace(re, replacement);
        }
        return subject;
    };

    const get_sub_varesatser = function (varesats) {
        const subs = [];
        const id = varesats["id"];
        for (let kode in varesatser) {
            subsats = varesatser[kode]
            if (subsats["overordnet"] === id) {
                subs.push(subsats);
            }
        }
        return subs;
    }

    const get_afgiftssats_text = function (varesats) {
        const enhed = varesats["enhed"];
        /*if (enhed === "sam") {
            const tekster = [];
            for (let subsats of get_sub_varesatser(varesats)) {
                tekster.push(get_afgiftssats_text(subsats))
            }
            return tekster.join(" + ");
        }*/
        return satsTekster[enhed].replace("%f", formatMoney(varesats["afgiftssats"]))
    }

    const formatMoney = function(value) {
        if (typeof(value) !== "number") {
            value = parseFloat(value);
        }
        let intPart = String(Math.floor(value));
        let floatPart = String((value - Math.floor(value)).toPrecision(2));
        intPart = replace_repeat(intPart, /^(-?\d+)(\d\d\d)(\.|,|$)/, '$1.$2$3');  // Starting from the right, prefix groups of 3 digits with a dot
        floatPart = floatPart.substring(2, 4).padEnd(2, "0")  // Get the two first digits of the decimal
        return intPart + "," + floatPart;
    }

    // Vis varekode ved ændring i dropdown
    // -----------------------------------
    const updateVareart = function(subform) {
        if (!subform) {
            subform = $(this);
        }
        if (!(subform instanceof $)) {
            subform = $(subform);
        }
        const vareafgiftssats = subform.find("[name$=vareafgiftssats]");
        const varesats = varesatser[vareafgiftssats.val()];
        const enhed = varesats["enhed"];
        const varekode = String(varesats["afgiftsgruppenummer"]).padStart(9, "0");
        subform.find("[data-value=varekode]").val(varekode);
        subform.find("[data-value=varekode]").attr("title", varekode);
        subform.find("[data-value=afgiftssats]").val(get_afgiftssats_text(varesats));
        subform.find("[data-value$=mængde]").toggle(enhed in ["kg", "l", "pct"]);
        subform.find("[data-value$=antal]").toggle(enhed in ["ant", "pct"]);
    };

    const container = $("#formset_container");


    const calcSubAfgift = function(varesats, kg_l, antal, beløb) {
        const afgiftssats = varesats["afgiftssats"]
        if (varesats["segment_øvre"]) {
            beløb = Math.min(beløb, varesats["segment_øvre"]);
        }
        if (varesats["segment_nedre"]) {
            beløb = Math.max(0, beløb - varesats["segment_nedre"]);
        }
        switch (varesats["enhed"]) {
            case "ant":
                return antal * afgiftssats;
            case "l":
            case "kg":
                return kg_l * afgiftssats;
            case "pct":
                return beløb * 0.01 * afgiftssats;
            case "sam":
                let afgift = 0
                for (let subsats of get_sub_varesatser(varesats)) {
                    afgift += calcSubAfgift(subsats, kg_l, antal, beløb)
                }
                return afgift;
        }
    }

    const calcAfgift = function (subform) {
        if (!(subform instanceof $)) {
            subform = $(subform);
        }
        const vareafgiftssats = subform.find("[name$=vareafgiftssats]");
        const varesats = varesatser[vareafgiftssats.val()];
        const afgift = calcSubAfgift(
            varesats,
            parseInt(subform.find("[name$=mængde]").val()),
            parseInt(subform.find("[name$=antal]").val()),
            parseInt(subform.find("[name$=fakturabeløb]").val()),
        );

        subform.find("[data-value=afgiftsbeløb]").val(
            isNaN(afgift) ? "" : formatMoney(afgift)
        );
        subform.data("afgift", isNaN(afgift) ? null : afgift);
        calcAfgiftSum();
    };
    const calcAfgiftSum = function() {
        let totalAfgift = 0;
        container.find(".row").each(function () {
            const afgift = $(this).data("afgift");
            if (afgift !== null) {
                totalAfgift += afgift;
            }
        });
        $("[data-value=sum-afgiftsbeløb]").val(formatMoney(totalAfgift));
    };

    // Formset
    // -------
    const formset = container.formset("form", $("#formset_prototype"));
    const subformAdded = function(subform) {
        if (!(subform instanceof $)) {
            subform = $(subform);
        }
        subform.find(".remove-row").click(removeForm.bind(subform, subform));
        subform.find("[name$=vareafgiftssats]").on("change", updateVareart.bind(subform, subform));
        subform.find("input,select").on("change", calcAfgift.bind(subform, subform));
        updateVareart(subform);
        calcAfgift(subform);
    };
    const subformRemoved = function(subform) {
        calcAfgiftSum();
        container.find(".row").each(function (index, element) {
            $(this).find("input[name],select[name]").each(function (){
                this.id = this.id.replace(/-\d+-/, "-"+index+"-");
                this.name = this.name.replace(/-\d+-/, "-"+index+"-");
            });
        });
    };

    const addForm = function () {
        const newForm = formset.addForm();
        subformAdded(newForm);
    };
    const removeForm = function(subform) {
        formset.removeForm(subform, true);
        subformRemoved(subform);
    };
    $("#formset_add").click(addForm);
    container.find(".row").each(function (){subformAdded(this)});

    // Filefield
    // ---------
    const fileUpdate = function() {
        // Validér filstørrelse
        if (this.files.length) {
            const maxsize = this.getAttribute("max_size");
            const filesize = this.files[0].size;
            if (maxsize && filesize > maxsize) {
                this.setCustomValidity(this.getAttribute("data-validity-sizeoverflow"));
            } else {
                this.setCustomValidity("");
            }
        }
    };
    const fileInputs = $("input[type=file]");
    fileInputs.change(fileUpdate);
    fileInputs.each(fileUpdate);
});
$(function () {
    // Custom-fejlbeskeder i klientvalidering
    const validity_checks = ["rangeUnderflow", "rangeOverflow"];
    const find = validity_checks.map((check) => "input[data-validity-"+check.toLowerCase()+"]").join(",");
    $(find).on("input", function() {
        this.checkValidity();
        for (let check of validity_checks) {
            if (this.validity[check]) {
                this.setCustomValidity(this.getAttribute("data-validity-" + check.toLowerCase()));
                return true;
            }
        }
        this.setCustomValidity("");
        return false;
    });
});
