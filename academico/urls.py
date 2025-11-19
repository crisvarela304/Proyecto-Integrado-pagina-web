from django.urls import path
from . import views
from .profesor_views import (
    panel_profesor, mis_estudiantes_profesor, gestionar_calificaciones,
    enviar_correos, registro_asistencias, estadisticas_profesor
)

app_name = 'academico'

urlpatterns = [
    # Dashboard principal académico
    path('dashboard/', views.dashboard_academico, name='dashboard_academico'),
    
    # Vistas para estudiantes
    path('calificaciones/', views.mis_calificaciones, name='mis_calificaciones'),
    path('horario/', views.mi_horario, name='mi_horario'),
    path('asistencias/', views.mis_asistencias, name='mis_asistencias'),
    path('cursos/', views.mis_cursos, name='mis_cursos'),
    path('asignaturas/', views.mis_asignaturas, name='mis_asignaturas'),
    
    # Vistas específicas para profesores
    path('profesor/', panel_profesor, name='panel_profesor'),
    path('profesor/estudiantes/', mis_estudiantes_profesor, name='mis_estudiantes_profesor'),
    path('profesor/calificaciones/<int:estudiante_id>/', gestionar_calificaciones, name='gestionar_calificaciones'),
    path('profesor/correos/', enviar_correos, name='enviar_correos'),
    path('profesor/asistencias/<int:curso_id>/', registro_asistencias, name='registro_asistencias'),
    path('profesor/estadisticas/', estadisticas_profesor, name='estadisticas_profesor'),
]
