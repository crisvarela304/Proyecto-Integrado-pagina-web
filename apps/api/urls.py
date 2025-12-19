"""
URLs de la API REST para Schoolar OS
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, CustomTokenRefreshView,
    AlumnoProfileView, AlumnoNotasView, AlumnoAsistenciaView,
    AlumnoHorarioView, AlumnoAnotacionesView, AlumnoTareasView, AlumnoEntregasView,
    NotificacionesListView, NotificacionMarcarLeidaView,
    ColegioDiscoverView, ApoderadoPupilosView
)

app_name = 'api'

urlpatterns = [
    # ==========================================================================
    # AUTENTICACIÓN
    # ==========================================================================
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # ==========================================================================
    # ALUMNO
    # ==========================================================================
    path('alumno/me/', AlumnoProfileView.as_view(), name='alumno_profile'),
    path('alumno/me/notas/', AlumnoNotasView.as_view(), name='alumno_notas'),
    path('alumno/me/asistencia/', AlumnoAsistenciaView.as_view(), name='alumno_asistencia'),
    path('alumno/me/horario/', AlumnoHorarioView.as_view(), name='alumno_horario'),
    path('alumno/me/anotaciones/', AlumnoAnotacionesView.as_view(), name='alumno_anotaciones'),
    
    # ==========================================================================
    # NOTIFICACIONES
    # ==========================================================================
    path('notificaciones/', NotificacionesListView.as_view(), name='notificaciones_list'),
    path('notificaciones/<uuid:uuid>/leer/', NotificacionMarcarLeidaView.as_view(), name='notificacion_leer'),
    
    # ==========================================================================
    # TAREAS
    # ==========================================================================
    path('alumno/me/tareas/', AlumnoTareasView.as_view(), name='alumno_tareas'),
    path('alumno/me/entregas/', AlumnoEntregasView.as_view(), name='alumno_entregas'),
    
    # ==========================================================================
    # APODERADO
    # ==========================================================================
    path('apoderado/pupilos/', ApoderadoPupilosView.as_view(), name='apoderado_pupilos'),
    
    # ==========================================================================
    # COLEGIO - PHONE HOME
    # ==========================================================================
    path('colegio/discover/', ColegioDiscoverView.as_view(), name='colegio_discover'),
]
