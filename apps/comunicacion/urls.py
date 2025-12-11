from django.urls import path
from .views import (
    noticias_list, 
    noticia_detalle, 
    noticias_privadas, 
    estadisticas_noticias,
    gestion_noticias,
    crear_noticia,
    editar_noticia,
    eliminar_noticia
)

app_name = 'comunicacion'

urlpatterns = [
    path('', noticias_list, name='noticias'),
    path('<int:pk>/', noticia_detalle, name='noticia_detalle'),
    path('privadas/', noticias_privadas, name='noticias_privadas'),
    path('estadisticas/', estadisticas_noticias, name='estadisticas_noticias'),
    
    # Gestión administrativa
    path('gestion/', gestion_noticias, name='gestion_noticias'),
    path('crear/', crear_noticia, name='crear_noticia'),
    path('editar/<int:pk>/', editar_noticia, name='editar_noticia'),
    path('eliminar/<int:pk>/', eliminar_noticia, name='eliminar_noticia'),
]
