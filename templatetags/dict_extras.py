"""
Filtros personalizados para manipulación de diccionarios en templates de Django
"""

from django import template

register = template.Library()

@register.filter
def dict_key(dict, key):
    """Obtiene un valor de un diccionario usando la clave"""
    try:
        return dict.get(key, '')
    except (AttributeError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario o lista"""
    try:
        if isinstance(dictionary, dict):
            return dictionary.get(key, '')
        elif isinstance(dictionary, list) and isinstance(key, int):
            return dictionary[key] if 0 <= key < len(dictionary) else ''
        else:
            return ''
    except (AttributeError, TypeError, IndexError):
        return ''

@register.filter
def add_suffix(value, suffix):
    """Agrega un sufijo a un valor"""
    return f"{value}{suffix}"

@register.filter
def subtract(value, arg):
    """Resta arg de value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplica value por arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value por arg"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def mod(value, arg):
    """Calcula el módulo de value divided by arg"""
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError):
        return 0
