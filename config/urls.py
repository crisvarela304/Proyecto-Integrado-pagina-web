from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import error_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),        # Página de inicio
    path('noticias/', include('comunicacion.urls')),  # Sistema noticias
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),      # Sistema usuarios
    path('academico/', include('academico.urls', namespace='academico')),    # Sistema académico
    path('documentos/', include('documentos.urls', namespace='documentos')),  # Sistema documentos
    path('mensajeria/', include('mensajeria.urls', namespace='mensajeria')),  # Sistema mensajería
]

# Handler personalizado para errores 404
handler404 = error_404

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
