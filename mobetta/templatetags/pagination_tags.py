from django import template

register = template.Library()


@register.assignment_tag
def apply(obj, method, *args):
    return getattr(obj, method)(*args)
