from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import error_404, error_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),        # Página de inicio
    path('noticias/', include('comunicacion.urls')),  # Sistema noticias
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),      # Sistema usuarios
    path('academico/', include('academico.urls', namespace='academico')),    # Sistema académico
    path('documentos/', include('documentos.urls', namespace='documentos')),  # Sistema documentos
    path('mensajeria/', include('mensajeria.urls', namespace='mensajeria')),  # Sistema mensajería
    path('panel-administrativo/', include('administrativo.urls', namespace='administrativo')), # LiceoOS Dashboard
    path('tareas/', include('tareas.urls', namespace='tareas')),  # Sistema de tareas
    path('calendario/', include('calendario.urls', namespace='calendario')),  # Calendario escolar
]

# Handlers personalizados para errores
handler404 = error_404
handler500 = error_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
