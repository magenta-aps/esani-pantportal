# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django import forms


class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            self.set_field_classes(name, field)

    def full_clean(self):
        result = super(BootstrapForm, self).full_clean()
        self.set_all_field_classes()
        return result

    def set_all_field_classes(self):
        for name, field in self.fields.items():
            self.set_field_classes(name, field, True)

    def set_field_classes(self, name, field, check_for_errors=False):
        classes = self.split_class(field.widget.attrs.get("class"))
        classes.append("mr-2")
        classes.append("form-control")
        if isinstance(field.widget, forms.Select):
            classes.append("form-select")

        if check_for_errors:
            if self.has_error(name) is True:
                classes.append("is-invalid")
        field.widget.attrs["class"] = " ".join(set(classes))

    @staticmethod
    def split_class(class_string):
        return class_string.split(" ") if class_string else []
