from django.urls import path
from .views import home, contacto, configuracion_sistema



urlpatterns = [
    path('', home, name='home'),
    path('contacto/', contacto, name='contacto'),
    path('configuracion/', configuracion_sistema, name='configuracion_sistema'),
]
