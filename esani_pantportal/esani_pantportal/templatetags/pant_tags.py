from django.template.defaultfilters import register


@register.filter
def verbose_name(item, field):
    return item._meta.get_field(field).verbose_name.title()
