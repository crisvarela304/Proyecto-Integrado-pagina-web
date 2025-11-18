"""
Template tags personalizados para mensajería segura
"""
from django import template
import os

register = template.Library()

@register.filter
def filename(value):
    """
    Filtro para obtener solo el nombre del archivo sin la ruta completa
    """
    if not value:
        return ""
    return os.path.basename(str(value))
