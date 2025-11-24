from django.urls import path
from .views import (
    registrar_usuario,
    login_usuario,
    login_profesor,
    login_estudiante,
    logout_usuario,
    panel,
    mi_perfil,
    cambiar_password
)

app_name = 'usuarios'

urlpatterns = [
    path('registrar/', registrar_usuario, name='registrar'),
    path('login/', login_usuario, name='login'),
    path('login/profesor/', login_profesor, name='login_profesor'),
    path('login/estudiante/', login_estudiante, name='login_estudiante'),
    path('logout/', logout_usuario, name='logout'),
    path('panel/', panel, name='panel'),
    path('perfil/', mi_perfil, name='mi_perfil'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
]
