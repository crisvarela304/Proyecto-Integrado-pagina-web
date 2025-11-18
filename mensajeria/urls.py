"""
URLs seguras para mensajería interna
Con nombres de URLs únicos y prevención de conflictos
"""
from django.urls import path
from . import views

app_name = 'mensajeria'

urlpatterns = [
    # Lista de conversaciones
    path('', views.conversaciones_list, name='conversaciones_list'),
    
    # Detalle de conversación
    path('conversacion/<int:conversacion_id>/', views.conversacion_detail, name='conversacion_detail'),
    
    # Crear nueva conversación
    path('nueva/', views.nueva_conversacion, name='nueva_conversacion'),
    
    # Endpoints AJAX
    path('conversacion/<int:conversacion_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('conversacion/<int:conversacion_id>/leido/', views.marcar_leido, name='marcar_leido'),
    
    # Eliminar conversación (solo alumnos)
    path('conversacion/<int:conversacion_id>/eliminar/', views.eliminar_conversacion, name='eliminar_conversacion'),
    
    # Mensajes destacados (solo profesores/staff)
    path('destacados/', views.mensajes_destacados, name='mensajes_destacados'),
]
