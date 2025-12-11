from django.urls import path
from .views import (
    registrar_usuario,
    login_usuario,
    login_profesor,
    login_estudiante,
    logout_usuario,
    panel,
    mi_perfil,
    cambiar_password,
    matricular_alumno_administrativo, # Vista administrativa
    gestion_usuarios, # Vista listado
    crear_usuario_rapido,
    editar_usuario,
    admin_reset_password,
    eliminar_usuario
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
    
    # Administrativo
    path('matricular/', matricular_alumno_administrativo, name='matricular_alumno'),
    path('gestion/', gestion_usuarios, name='gestion_usuarios'),
    path('crear/rapido/', crear_usuario_rapido, name='crear_usuario_rapido'),
    path('editar/<int:usuario_id>/', editar_usuario, name='editar_usuario'),
    path('admin-reset-password/', admin_reset_password, name='admin_reset_password'),
    path('eliminar/<int:usuario_id>/', eliminar_usuario, name='eliminar_usuario'),
]
