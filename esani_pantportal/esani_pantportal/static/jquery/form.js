$(function () {
    // Formset
    // -------
    const container = $("#formset_container");
    const formset = container.formset("form", $("#formset_prototype"));
    const subformAdded = function(subform) {
        if (!(subform instanceof $)) {
            subform = $(subform);
        }
        subform.find(".remove-row").click(removeForm.bind(subform, subform));
        const addButton = subform.find(".add-row");
        addButton.click(addForm);
        subformsUpdated();
    };
    const subformRemoved = function(subform) {
        const rows = container.find(".row");
        rows.each(function (index, element) {
            $(this).find("input[name],select[name]").each(function (){
                this.id = this.id.replace(/-\d+-/, "-"+index+"-");
                this.name = this.name.replace(/-\d+-/, "-"+index+"-");
            });
        });
        subformsUpdated();
    };
    const subformsUpdated = function () {
        const rows = container.find(".row");
        const lastRow = rows.last();
        lastRow.find(".add-row").show();
        if (rows.length === 1) {
            lastRow.find(".remove-row").hide();
        } else {
            rows.find(".remove-row").show();
            rows.not(lastRow).find(".add-row").hide();
        }
    }

    const addForm = function () {
        const newForm = formset.addForm();
        subformAdded(newForm);
    };
    const removeForm = function(subform) {
        formset.removeForm(subform, true);
        subformRemoved(subform);
    };
    container.find(".row").each(function (){subformAdded(this)});


    // Add row when the user presses the "+" button
    $(document).keypress(function(e){
        console.log(e.which)
        e.stopImmediatePropagation();
        if (e.which == 43){
            addForm();
        }
    });
});
