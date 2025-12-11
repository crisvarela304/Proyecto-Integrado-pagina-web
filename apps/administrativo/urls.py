from django.urls import path
from . import views

app_name = 'administrativo'

urlpatterns = [
    path('', views.dashboard_main, name='dashboard'),
    
    # Gestión de Cursos
    path('cursos/', views.gestion_cursos, name='gestion_cursos'),
    path('cursos/crear/', views.curso_crear, name='curso_crear'),
    path('cursos/editar/<int:pk>/', views.curso_editar, name='curso_editar'),
    path('cursos/eliminar/<int:pk>/', views.curso_eliminar, name='curso_eliminar'),
    
    # Carga Masiva (Alumnos y Profesores)
    path('carga-masiva/', views.carga_masiva_estudiantes, name='carga_masiva_estudiantes'),
    path('carga-masiva/profesores/', views.carga_masiva_profesores, name='carga_masiva_profesores'),
    path('descargar-plantilla/', views.descargar_plantilla_carga, name='descargar_plantilla_carga'),
    path('descargar-plantilla/<str:tipo>/', views.descargar_plantilla_carga, name='descargar_plantilla_carga_tipo'),
    
    # Auditoría
    path('historial/', views.historial_actividad, name='historial_actividad'),
    path('recursos/', views.monitor_recursos, name='monitor_recursos'),
]
