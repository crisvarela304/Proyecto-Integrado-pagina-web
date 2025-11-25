from django.urls import path
from .views import (
    noticias_list, 
    noticia_detalle, 
    noticias_privadas, 
    estadisticas_noticias
)

urlpatterns = [
    path('', noticias_list, name='noticias'),
    path('<int:pk>/', noticia_detalle, name='noticia_detalle'),
    path('privadas/', noticias_privadas, name='noticias_privadas'),
    path('estadisticas/', estadisticas_noticias, name='estadisticas_noticias'),
]
