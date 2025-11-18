from django.urls import path
from .views import (
    documentos_list,
    documento_detalle,
    descargar_documento,
    mis_documentos,
    examenes_calendario,
    comunicado_padres,
    subir_documento
)

app_name = 'documentos'

urlpatterns = [
    # Documentos
    path('', documentos_list, name='documentos_list'),
    path('<int:pk>/', documento_detalle, name='documento_detalle'),
    path('<int:pk>/descargar/', descargar_documento, name='descargar_documento'),
    path('mis/', mis_documentos, name='mis_documentos'),
    path('subir/', subir_documento, name='subir_documento'),
    
    # Exámenes
    path('examenes/', examenes_calendario, name='examenes_calendario'),
    
    # Comunicados
    path('comunicados/', comunicado_padres, name='comunicados_padres'),
]
