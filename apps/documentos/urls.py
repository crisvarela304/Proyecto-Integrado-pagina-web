from django.urls import path
from .views import (
    documentos_list,
    documento_detalle,
    descargar_documento,
    mis_documentos,
    # examenes_calendario,
    comunicado_padres,
    gestion_documentos,
    gestion_categorias_doc,
    eliminar_documento,
    eliminar_categoria,
    material_estudio,
)

app_name = 'documentos'

urlpatterns = [
    # Documentos
    path('', documentos_list, name='documentos_list'),
    path('<int:pk>/', documento_detalle, name='documento_detalle'),
    path('<int:pk>/descargar/', descargar_documento, name='descargar_documento'),
    path('mis/', mis_documentos, name='mis_documentos'),
    path('material-estudio/', material_estudio, name='material_estudio'),
    
    # Exámenes (Deshabilitado temporalmente por falta de modelo)
    # path('examenes/', examenes_calendario, name='examenes_calendario'),
    
    # Comunicados
    path('comunicados/', comunicado_padres, name='comunicados_padres'),

    # Gestión Administrativa
    path('gestion/', gestion_documentos, name='gestion_documentos'),
    path('gestion/<int:pk>/eliminar/', eliminar_documento, name='eliminar_documento'),
    path('categorias/', gestion_categorias_doc, name='gestion_categorias_doc'),
    path('categorias/<int:pk>/eliminar/', eliminar_categoria, name='eliminar_categoria'),
]
