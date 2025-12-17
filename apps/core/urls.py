from django.urls import path
from .views import (
    home, contacto, configuracion_sistema,
    notificaciones_json, marcar_notificacion_leida, marcar_todas_leidas
)



urlpatterns = [
    path('', home, name='home'),
    path('contacto/', contacto, name='contacto'),
    path('configuracion/', configuracion_sistema, name='configuracion_sistema'),
    
    # API Notificaciones
    path('api/notificaciones/', notificaciones_json, name='notificaciones_json'),
    path('api/notificaciones/<int:notificacion_id>/leer/', marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/notificaciones/leer-todas/', marcar_todas_leidas, name='marcar_todas_leidas'),
]
