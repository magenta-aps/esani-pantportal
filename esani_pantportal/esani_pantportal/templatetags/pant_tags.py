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


@register.filter
def get_display_name(obj, attr):
    """
    Returns the display name of an object field
    """

    try:
        return getattr(obj, f"get_{attr}_display")()
    except AttributeError:
        return getattr(obj, attr)


@register.filter
def parenthesized(string):
    return f"({string})"


@register.filter(name="has_group")
def has_group(user, group_name):
    if user.is_superuser:
        return True
    else:
        return user.groups.filter(name=group_name).exists()
