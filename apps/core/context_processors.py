"""
Context processors para información institucional global.
Requerido para cumplir con los requisitos del proyecto.
"""

from django.conf import settings
from .models import ConfiguracionAcademica
from django.apps import apps

def institucion_info(request):
    """
    Context processor que proporciona información institucional
    y notificaciones disponible en todas las plantillas del sitio.
    """
    try:
        config = ConfiguracionAcademica.get_actual()
        año_actual = config.año_actual
        semestre_actual = config.semestre_actual
        semestre_label = config.get_semestre_actual_display()
    except Exception:
        año_actual = 2024
        semestre_actual = '1'
        semestre_label = 'Primer Semestre'

    # Notificaciones de mensajería (lazy loading para evitar circular imports si fuera necesario)
    total_no_leidos = 0
    if request.user.is_authenticated:
        try:
            Mensaje = apps.get_model('mensajeria', 'Mensaje')
            total_no_leidos = Mensaje.objects.filter(receptor=request.user, leido=False).count()
        except Exception:
            pass

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
        'notificaciones': {
            'mensajes_no_leidos': total_no_leidos
        },
        'contacto_email': settings.INSTITUCION_INFO['email'],
        'pagina_personalizada': {
            'titulo_sitio': f"{settings.INSTITUCION_INFO['nombre']} - Portal Institucional",
            'descripcion': "Plataforma institucional para mejorar la comunicación entre el establecimiento, apoderados y estudiantes",
            'autor': "Liceo Juan Bautista de Hualqui",
        }
    }
