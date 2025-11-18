"""
Context processors para información institucional global.
Requerido para cumplir con los requisitos del proyecto.
"""

from django.conf import settings

def institucion_info(request):
    """
    Context processor que proporciona información institucional
    disponible en todas las plantillas del sitio.
    """
    return {
        'institucion': {
            'nombre': settings.INSTITUCION_INFO['nombre'],
            'direccion': settings.INSTITUCION_INFO['direccion'],
            'telefono': settings.INSTITUCION_INFO['telefono'],
            'email': settings.INSTITUCION_INFO['email'],
            'rbd': settings.INSTITUCION_INFO['rbd'],
            'anno_fundacion': settings.INSTITUCION_INFO['anno_fundacion'],
        },
        'contacto_email': settings.INSTITUCION_INFO['email'],
        'pagina_personalizada': {
            'titulo_sitio': f"{settings.INSTITUCION_INFO['nombre']} - Portal Institucional",
            'descripcion': "Plataforma institucional para mejorar la comunicación entre el establecimiento, apoderados y estudiantes",
            'autor': "Liceo Juan Bautista de Hualqui",
        }
    }
