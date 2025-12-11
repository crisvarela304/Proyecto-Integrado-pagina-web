from django import template

register = template.Library()

@register.simple_tag
def is_selected(current_value, target_value):
    """
    Returns 'selected' if current_value matches target_value.
    Handles string vs int comparison safely.
    """
    if str(current_value) == str(target_value):
        return 'selected'
    return ''
