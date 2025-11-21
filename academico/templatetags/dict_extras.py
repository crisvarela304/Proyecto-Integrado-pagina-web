from django import template

register = template.Library()


@register.filter
def get_item(value, key):
    """Obtiene un item desde dict o lista por clave/index."""
    try:
        if isinstance(value, dict):
            return value.get(key)
        return value[key]
    except Exception:
        return ""


@register.filter(name="dict_key")
def dict_key(value, key):
    """
    Permite hacer: mi_dict|dict_key:llave
    Devuelve mi_dict[llave] o mi_dict.get(llave), o "" si no existe.
    También funciona con listas e índices.
    """
    try:
        if isinstance(value, dict):
            return value.get(key)
        return value[key]
    except Exception:
        return ""


@register.filter
def add_suffix(value, suffix):
    """Agrega un sufijo a un valor."""
    try:
        return f"{value}{suffix}"
    except Exception:
        return value


@register.filter
def subtract(value, arg):
    """Resta arg de value."""
    try:
        return int(value) - int(arg)
    except Exception:
        return 0


@register.filter
def multiply(value, arg):
    """Multiplica value por arg."""
    try:
        return float(value) * float(arg)
    except Exception:
        return 0


@register.filter
def divide(value, arg):
    """Divide value por arg evitando division por cero."""
    try:
        arg_val = float(arg)
        return float(value) / arg_val if arg_val != 0 else 0
    except Exception:
        return 0


@register.filter
def mod(value, arg):
    """Calcula el modulo de value dividido por arg."""
    try:
        return int(value) % int(arg)
    except Exception:
        return 0
