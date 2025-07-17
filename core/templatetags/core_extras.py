from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    return dictionary.get(key)

@register.filter
def sub(value, arg):
    """Subtract the argument from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value