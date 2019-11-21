from collections import OrderedDict

from django import template


register = template.Library()


option_dict = OrderedDict({"1": "Not Valid",
                           "2": "Simple/Incomplete",
                           "3": "Simple/Complete",
                           "4": "Complex/Incomplete",
                           "5": "Complex/Complete"})


@register.simple_tag
def get_options():
    return option_dict


@register.filter
def filter_options(key):
    if key in option_dict:
        return option_dict[key]
    return None
