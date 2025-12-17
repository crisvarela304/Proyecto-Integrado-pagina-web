from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.calendario_publico, name='calendario'),
    path('mi-calendario/', views.calendario_usuario, name='mi_calendario'),
    path('api/eventos/', views.eventos_json, name='eventos_json'),
    path('api/crear/', views.crear_evento, name='crear_evento'),
]
