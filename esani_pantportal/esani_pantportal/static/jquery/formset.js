$(function(){
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    $.fn.extend({
        'formset': function(name, formPrototypeContainer) {
            const management = {
                total: $('#id_'+name+'-TOTAL_FORMS'),
                initial: $('#id_'+name+'-INITIAL_FORMS'),
                min: $('#id_'+name+'-MIN_NUM_FORMS'),
                max: $('#id_'+name+'-MAX_NUM_FORMS')
            };
            const formContainer = this;
            const formPrototype = formPrototypeContainer.children().first();

            const updateTotal = function() {
                management.total.val(formContainer.children().length);
            };

            const addForm = function(update) {
                const form = formPrototype.clone();
                const nextId = parseInt(management.total.val());
                form.find('*').each(function() {
                    for (let i = 0; i < this.attributes.length; i++) {
                        this.attributes[i].nodeValue = this.attributes[i].nodeValue.replace('__prefix__', nextId);
                    }
                });
                formContainer.trigger("subform.pre_add", form);
                formContainer.append(form);
                formContainer.trigger("subform.post_add", form);
                if (update !== false) {
                    updateTotal();
                }
                return form;
            };

            const removeForm = function(form, update) {
                if (form.parent().first().is(formContainer)) {
                    const parent = form.parent();
                    form.trigger("subform.pre_remove");
                    form.remove();
                    if (update !== false) {
                        updateTotal();
                    }
                    parent.trigger("subform.post_remove", form);
                }
            };

            return {
                'addForm': addForm,
                'removeForm': removeForm
            }
        }
    });
});

