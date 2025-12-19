"""
Utilidades para la API REST
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Manejador personalizado de excepciones que sigue el contrato estándar:
    {
        "success": false,
        "data": null,
        "message": "Error description",
        "errors": {...}
    }
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'success': False,
            'data': None,
            'message': str(exc),
            'errors': response.data if isinstance(response.data, dict) else {'detail': response.data}
        }
        response.data = custom_response
    
    return response


def api_response(data=None, message='OK', success=True, status=200):
    """
    Helper para crear respuestas API estándar
    """
    return Response({
        'success': success,
        'data': data,
        'message': message,
        'errors': None
    }, status=status)


def api_error(message, errors=None, status=400):
    """
    Helper para crear respuestas de error estándar
    """
    return Response({
        'success': False,
        'data': None,
        'message': message,
        'errors': errors or {}
    }, status=status)
