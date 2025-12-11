from django.urls import path
from . import views
from .profesor_views import (
    panel_profesor, mis_estudiantes_profesor, gestionar_calificaciones,
    enviar_correos, registro_asistencias, estadisticas_profesor,
    lista_calificaciones_profesor, gestionar_recursos, subir_recurso,
    eliminar_recurso, descargar_recurso
)

app_name = 'academico'

urlpatterns = [
    # Dashboard principal académico
    path('dashboard/', views.dashboard_academico, name='dashboard_academico'),
    
    # Vistas para estudiantes
    path('calificaciones/', views.mis_calificaciones, name='mis_calificaciones'),
    path('informe-notas/', views.descargar_informe_notas, name='descargar_informe_notas'),
    path('certificado-regular/', views.descargar_certificado_alumno_regular, name='descargar_certificado_alumno_regular'),
    path('certificados/', views.mis_certificados, name='mis_certificados'),
    path('certificados/descargar/<str:tipo>/', views.descargar_certificado_pdf, name='descargar_certificado_pdf'),
    path('horario/', views.mi_horario, name='mi_horario'),
    path('asistencias/', views.mis_asistencias, name='mis_asistencias'),
    path('cursos/', views.mis_cursos, name='mis_cursos'),
    path('asignaturas/', views.mis_asignaturas, name='mis_asignaturas'),
    path('curso/<int:curso_id>/notas/', views.registrar_notas_curso, name='registrar_notas_curso'),
    path('curso/<int:curso_id>/asistencia/', views.tomar_asistencia, name='tomar_asistencia'),
    path('estudiante/<int:pk>/', views.detalle_estudiante, name='detalle_estudiante'),
    
    # Vistas específicas para profesores
    path('profesor/', panel_profesor, name='panel_profesor'),
    path('profesor/estudiantes/', mis_estudiantes_profesor, name='mis_estudiantes_profesor'),
    path('profesor/calificaciones/', lista_calificaciones_profesor, name='lista_calificaciones_profesor'),
    path('profesor/calificaciones/<int:estudiante_id>/', gestionar_calificaciones, name='gestionar_calificaciones'),
    path('profesor/correos/', enviar_correos, name='enviar_correos'),
    path('profesor/asistencias/<int:curso_id>/', registro_asistencias, name='registro_asistencias'),
    path('profesor/estadisticas/', estadisticas_profesor, name='estadisticas_profesor'),
    
    # Recursos Académicos
    path('profesor/recursos/', gestionar_recursos, name='gestionar_recursos'),
    path('profesor/recursos/subir/', subir_recurso, name='subir_recurso'),
    path('profesor/recursos/eliminar/<int:pk>/', eliminar_recurso, name='eliminar_recurso'),
    path('recursos/descargar/<int:pk>/', descargar_recurso, name='descargar_recurso'),
    
    # Anotaciones (Hoja de Vida)
    path('anotaciones/mis-anotaciones/', views.mis_anotaciones, name='mis_anotaciones'),
    path('anotaciones/crear/<int:estudiante_id>/', views.crear_anotacion, name='crear_anotacion'),
    path('anotaciones/historial/<int:estudiante_id>/', views.historial_anotaciones_estudiante, name='historial_anotaciones'),
    
    # Importación masiva
    # Importación masiva
    path('importar-estudiantes/', views.importar_estudiantes, name='importar_estudiantes'),
    
    # Gestión Administrativa
    path('gestion-cursos/', views.gestion_cursos, name='gestion_cursos'),
    path('gestion-cursos/editar/<int:curso_id>/', views.editar_curso, name='editar_curso'),
    path('gestion-cursos/inscripciones/<int:curso_id>/', views.curso_inscripciones, name='curso_inscripciones'),
    path('gestion-asignaturas/', views.gestion_asignaturas, name='gestion_asignaturas'),
    path('asignaturas/<int:asignatura_id>/editar/', views.editar_asignatura, name='editar_asignatura'),
    path('asignaturas/<int:asignatura_id>/eliminar/', views.eliminar_asignatura, name='eliminar_asignatura'),
]
