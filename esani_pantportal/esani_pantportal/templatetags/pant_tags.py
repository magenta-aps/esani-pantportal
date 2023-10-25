from urllib.parse import quote

from django.template.defaultfilters import register


@register.filter
def verbose_name(item, field):
    return item._meta.get_field(field).verbose_name.title()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def quote_url(url):
    return quote(url)
