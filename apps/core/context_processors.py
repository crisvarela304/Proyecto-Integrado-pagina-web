"""
Context processors para información institucional global.
Requerido para cumplir con los requisitos del proyecto.
"""

from django.conf import settings
from .models import ConfiguracionAcademica

def institucion_info(request):
    """
    Context processor que proporciona información institucional
    disponible en todas las plantillas del sitio.
    """
    try:
        config = ConfiguracionAcademica.get_actual()
        año_actual = config.año_actual
        semestre_actual = config.semestre_actual
        semestre_label = config.get_semestre_actual_display()
    except:
        año_actual = 2024
        semestre_actual = '1'
        semestre_label = 'Primer Semestre'

    return {
        'institucion': {
            'nombre': settings.INSTITUCION_INFO['nombre'],
            'direccion': settings.INSTITUCION_INFO['direccion'],
            'telefono': settings.INSTITUCION_INFO['telefono'],
            'email': settings.INSTITUCION_INFO['email'],
            'rbd': settings.INSTITUCION_INFO['rbd'],
            'anno_fundacion': settings.INSTITUCION_INFO['anno_fundacion'],
        },
        'configuracion_academica': {
            'año_actual': año_actual,
            'semestre_actual': semestre_actual,
            'semestre_label': semestre_label,
        },
        'contacto_email': settings.INSTITUCION_INFO['email'],
        'pagina_personalizada': {
            'titulo_sitio': f"{settings.INSTITUCION_INFO['nombre']} - Portal Institucional",
            'descripcion': "Plataforma institucional para mejorar la comunicación entre el establecimiento, apoderados y estudiantes",
            'autor': "Liceo Juan Bautista de Hualqui",
        }
    }
