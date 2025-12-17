from django.urls import path
from . import views

app_name = 'tareas'

urlpatterns = [
    # Profesor
    path('profesor/', views.lista_tareas_profesor, name='lista_tareas_profesor'),
    path('profesor/crear/', views.crear_tarea, name='crear_tarea'),
    path('profesor/tarea/<int:tarea_id>/entregas/', views.ver_entregas, name='ver_entregas'),
    path('profesor/entrega/<int:entrega_id>/calificar/', views.calificar_entrega, name='calificar_entrega'),
    
    # Estudiante
    path('mis-tareas/', views.mis_tareas, name='mis_tareas'),
    path('entregar/<int:tarea_id>/', views.entregar_tarea, name='entregar_tarea'),
]
