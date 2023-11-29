from urllib.parse import quote

from django.template.defaultfilters import register
from django.utils.translation import gettext_lazy as _

from esani_pantportal.models import USER_TYPE_CHOICES


@register.filter
def verbose_name(item, field):
    return item._meta.get_field(field).verbose_name.title()


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
        return str(getattr(obj, attr) or _("Udefineret"))


@register.filter(name="has_group")
def has_group(user, group_name):
    return True if user.is_superuser else user.groups.filter(name=group_name).exists()


@register.filter
def user_type(user_type_id):
    for c in USER_TYPE_CHOICES:
        if c[0] == user_type_id:
            return c[1]


@register.filter
def is_user_object(obj):
    return True if obj._meta.verbose_name.endswith("user") else False
