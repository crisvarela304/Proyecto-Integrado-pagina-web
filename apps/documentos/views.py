from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
import os
import mimetypes
from .models import Documento, CategoriaDocumento, HistorialDescargas, ComunicadoPadres
from .forms import DocumentoForm

# --- Vistas Administrativas ---

@login_required
def gestion_documentos(request):
    """Gestión administrativa de documentos"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    if not es_admin:
        return redirect('documentos:documentos_list')

    if request.method == 'POST':
        # Subida rápida desde el modal usando el Form para inferir tipo
        form = DocumentoForm(request.POST, request.FILES, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento subido correctamente.")
            return redirect('documentos:gestion_documentos')
        else:
            messages.error(request, "Error al subir el documento. Verifica los datos.")

    documentos = Documento.objects.select_related('categoria', 'creado_por').order_by('-fecha_creacion')
    categorias = CategoriaDocumento.objects.filter(activa=True)
    
    return render(request, 'documentos/gestion_documentos.html', {
        'documentos': documentos,
        'categorias': categorias
    })

@login_required
def eliminar_documento(request, pk):
    """Eliminar documento"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    if not es_admin:
        return redirect('home')
        
    doc = get_object_or_404(Documento, pk=pk)
    doc.delete()
    messages.success(request, "Documento eliminado.")
    return redirect('documentos:gestion_documentos')

@login_required
def gestion_categorias_doc(request):
    """Gestión de categorías de documentos"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    if not es_admin:
        return redirect('home')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            CategoriaDocumento.objects.get_or_create(nombre=nombre)
            messages.success(request, "Categoría creada.")
            return redirect('documentos:gestion_categorias_doc')
            
    categorias = CategoriaDocumento.objects.all().annotate(num_docs=Count('documentos'))
    return render(request, 'documentos/gestion_categorias.html', {'categorias': categorias})

@login_required
def eliminar_categoria(request, pk):
    cat = get_object_or_404(CategoriaDocumento, pk=pk)
    cat.delete()
    messages.success(request, "Categoría eliminada.")
    return redirect('documentos:gestion_categorias_doc')

# --- Vistas Públicas/Usuarios ---


def documentos_list(request):
    """Lista de documentos con filtros"""
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    visibilidad = request.GET.get('visibilidad', '').strip()
    
    # Query base
    qs = Documento.objects.filter(publicado=True)
    
    # Filtro de visibilidad basado en el tipo de usuario
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)
        if perfil:
            if perfil.tipo_usuario == 'estudiante':
                qs = qs.filter(Q(visibilidad='publico') | Q(visibilidad='solo_estudiantes'))
            elif perfil.tipo_usuario == 'profesor':
                qs = qs.filter(Q(visibilidad='publico') | Q(visibilidad='solo_profesores'))
            elif perfil.tipo_usuario in ['administrativo', 'directivo']:
                qs = qs.filter(visibilidad__in=['publico', 'solo_administrativos'])
            else:
                qs = qs.filter(visibilidad='publico')
    else:
        qs = qs.filter(visibilidad='publico')
    
    # Aplicar otros filtros
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) | 
            Q(descripcion__icontains=q) | 
            Q(tags__icontains=q)
        )
    
    if categoria:
        qs = qs.filter(categoria__id=categoria)
    
    if tipo:
        qs = qs.filter(tipo=tipo)
    
    if visibilidad:
        qs = qs.filter(visibilidad=visibilidad)
    
    # Paginación
    paginator = Paginator(qs.order_by('-fecha_creacion'), 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Contexto con selection logic
    
    # Categorías
    categorias_qs = CategoriaDocumento.objects.filter(activa=True)
    categorias_list = []
    target_categoria_id = int(categoria) if categoria.isdigit() else None
    
    for cat in categorias_qs:
        cat.is_selected = (cat.id == target_categoria_id)
        categorias_list.append(cat)
        
    # Tipos Documento
    tipos_doc_list = []
    for valor, texto in Documento.TIPO_CHOICES:
        tipos_doc_list.append({
            'valor': valor,
            'texto': texto,
            'is_selected': (valor == tipo)
        })
        
    # Visibilidad
    visibilidad_list = []
    for valor, texto in Documento.VISIBILIDAD_CHOICES:
        visibilidad_list.append({
            'valor': valor,
            'texto': texto,
            'is_selected': (valor == visibilidad)
        })
    
    return render(request, "documentos/documentos_list.html", {
        "page_obj": page_obj,
        "query": q,
        "categoria_filtro": categoria, # Mantener por si acaso
        "tipo_filtro": tipo,
        "visibilidad_filtro": visibilidad,
        "categorias_list": categorias_list,
        "tipos_doc_list": tipos_doc_list,
        "visibilidad_list": visibilidad_list
    })

def documento_detalle(request, pk):
    """Detalle de un documento"""
    documento = get_object_or_404(Documento, pk=pk, publicado=True)
    
    # Verificar permisos de visibilidad
    if documento.visibilidad != 'publico':
        if not request.user.is_authenticated:
            messages.error(request, "No tienes permisos para ver este documento.")
            return redirect('documentos:documentos_list')
        
        perfil = getattr(request.user, 'perfil', None)
        if not perfil:
            messages.error(request, "No tienes permisos para ver este documento.")
            return redirect('documentos:documentos_list')
        
        if documento.visibilidad == 'solo_estudiantes' and perfil.tipo_usuario != 'estudiante':
            messages.error(request, "No tienes permisos para ver este documento.")
            return redirect('documentos:documentos_list')
        elif documento.visibilidad == 'solo_profesores' and perfil.tipo_usuario != 'profesor':
            messages.error(request, "No tienes permisos para ver este documento.")
            return redirect('documentos:documentos_list')
        elif documento.visibilidad == 'solo_administrativos' and perfil.tipo_usuario not in ['administrativo', 'directivo']:
            messages.error(request, "No tienes permisos para ver este documento.")
            return redirect('documentos:documentos_list')
    
    # Documentos relacionados
    relacionados = Documento.objects.filter(
        categoria=documento.categoria,
        publicado=True
    ).exclude(pk=documento.pk).order_by('-fecha_creacion')[:6]

    tags = [tag.strip() for tag in (documento.tags or '').split(',') if tag.strip()]

    return render(request, "documentos/documento_detalle.html", {
        "documento": documento,
        "documentos_relacionados": relacionados,
        "tags": tags
    })

@login_required
def descargar_documento(request, pk):
    """Descargar un documento y registrar la descarga"""
    documento = get_object_or_404(Documento, pk=pk, publicado=True)
    
    # Verificar permisos
    if documento.visibilidad != 'publico':
        perfil = getattr(request.user, 'perfil', None)
        if not perfil:
            return HttpResponse("No autorizado", status=403)
        
        if documento.visibilidad == 'solo_estudiantes' and perfil.tipo_usuario != 'estudiante':
            return HttpResponse("No autorizado", status=403)
        elif documento.visibilidad == 'solo_profesores' and perfil.tipo_usuario != 'profesor':
            return HttpResponse("No autorizado", status=403)
        elif documento.visibilidad == 'solo_administrativos' and perfil.tipo_usuario not in ['administrativo', 'directivo']:
            return HttpResponse("No autorizado", status=403)
    
    if not documento.archivo:
        raise Http404("Archivo no encontrado")
    
    # Registrar descarga
    HistorialDescargas.objects.create(
        documento=documento,
        usuario=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Incrementar contador
    documento.descargar_count += 1
    documento.save(update_fields=['descargar_count'])
    
    # Preparar respuesta
    try:
        file_path = documento.archivo.path
        mime_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(open(file_path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name}"'
        return response
    except FileNotFoundError:
        raise Http404("Archivo no encontrado en el servidor")

@login_required
def mis_documentos(request):
    """Documentos subidos por el usuario actual"""
    qs = Documento.objects.filter(creado_por=request.user).order_by('-fecha_creacion')
    
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    return render(request, "documentos/documentos_list.html", {
        "page_obj": page_obj
    })

# @login_required
# def examenes_calendario(request):
#     """Calendario de exámenes"""
#     qs = Examen.objects.filter(activo=True)
#     
#     # Filtros
#     curso_id = request.GET.get('curso', '').strip()
#     asignatura_id = request.GET.get('asignatura', '').strip()
#     fecha_desde = request.GET.get('fecha_desde', '').strip()
#     fecha_hasta = request.GET.get('fecha_hasta', '').strip()
#     
#     # Aplicar filtros
#     if curso_id:
#         qs = qs.filter(curso_id=curso_id)
#     
#     if asignatura_id:
#         qs = qs.filter(asignatura_id=asignatura_id)
#     
#     if fecha_desde:
#         qs = qs.filter(fecha_aplicacion__gte=fecha_desde)
#     
#     if fecha_hasta:
#         qs = qs.filter(fecha_aplicacion__lte=fecha_hasta)
#     
#     # Filtrar por permisos del usuario
#     perfil = getattr(request.user, 'perfil', None)
#     if perfil:
#         if perfil.tipo_usuario == 'estudiante':
#             # Solo exámenes de los cursos donde está inscrito
#             from academico.models import InscripcionCurso
#             mis_cursos = InscripcionCurso.objects.filter(
#                 estudiante=request.user, 
#                 estado='activo'
#             ).values_list('curso_id', flat=True)
#             qs = qs.filter(curso_id__in=mis_cursos)
#         elif perfil.tipo_usuario == 'profesor':
#             # Solo exámenes que él creó
#             qs = qs.filter(profesor=request.user)
#     
#     qs = qs.order_by('fecha_aplicacion', 'hora_inicio')
#     
#     # Importar modelos necesarios para filtros
#     from academico.models import Curso, Asignatura
#     
#     return render(request, "documentos/examenes_calendario.html", {
#         "examenes": qs,
#         "cursos": Curso.objects.all(),
#         "asignaturas": Asignatura.objects.all(),
#         "filtros": {
#             "curso": curso_id,
#             "asignatura": asignatura_id,
#             "fecha_desde": fecha_desde,
#             "fecha_hasta": fecha_hasta
#         }
#     })

@login_required
def comunicado_padres(request):
    """Comunicados dirigidos a padres y apoderados"""
    qs = ComunicadoPadres.objects.filter(activo=True)
    
    # Filtrar por permisos y alcance
    perfil = getattr(request.user, 'perfil', None)
    if perfil:
        if perfil.tipo_usuario in ['estudiante']:
            qs = qs.filter(Q(dirigido_a__in=['todos', 'estudiantes']) | 
                         Q(cursos_objetivo__isnull=True) |
                         Q(cursos_objetivo__in=[]))
        elif perfil.tipo_usuario in ['apoderado', 'padres']:
            qs = qs.filter(Q(dirigido_a__in=['todos', 'padres', 'apoderados']) | 
                         Q(cursos_objetivo__isnull=True))
        else:
            # Profesores y administrativos ven todo
            pass
    
    # Filtrar por cursos específicos
    if perfil and perfil.tipo_usuario == 'estudiante':
        from academico.models import InscripcionCurso
        mis_cursos = InscripcionCurso.objects.filter(
            estudiante=request.user, 
            estado='activo'
        ).values_list('curso_id', flat=True)
        qs = qs.filter(Q(cursos_objetivo__isnull=True) | Q(cursos_objetivo__in=mis_cursos))
    
    qs = qs.order_by('-fecha_publicacion', '-urgencia')
    
    return render(request, "documentos/documentos_list.html", {
        "comunicados": qs
    })

@login_required
def subir_documento(request):
    """Subir un nuevo documento"""
    perfil = getattr(request.user, 'perfil', None)
    if not (request.user.is_staff or (perfil and perfil.tipo_usuario == 'profesor')):
        messages.error(request, "No tienes permisos para subir documentos.")
        return redirect('documentos:documentos_list')

    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, usuario=request.user)
        if form.is_valid():
            documento = form.save()
            messages.success(request, "Documento subido exitosamente.")
            return redirect(documento.get_absolute_url())
    else:
        form = DocumentoForm(usuario=request.user)
    
@login_required
def material_estudio(request):
    """Vista exclusiva para estudiantes: Material de Estudio"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'estudiante':
        messages.error(request, "Esta sección es solo para estudiantes.")
        return redirect('home')

    # Obtener cursos del estudiante
    from academico.models import InscripcionCurso
    mis_cursos_ids = InscripcionCurso.objects.filter(
        estudiante=request.user,
        estado='activo'
    ).values_list('curso_id', flat=True)

    # Filtrar documentos:
    # 1. Categoría "Material de Estudio" (o similar)
    # 2. Visibilidad permitida
    # 3. Asignados a sus cursos O generales (curso=None)
    
    # Intentar obtener la categoría con variaciones de nombre para ser robusto
    categorias_estudio = CategoriaDocumento.objects.filter(
        Q(nombre__icontains="estudio") | Q(nombre__icontains="material") | Q(nombre__icontains="guía")
    )
    
    qs = Documento.objects.filter(
        publicado=True,
        categoria__in=categorias_estudio
    ).filter(
        # Visibilidad
        Q(visibilidad='publico') | Q(visibilidad='solo_estudiantes')
    ).filter(
        # Cursos: Específico de su curso O Global
        Q(curso__id__in=mis_cursos_ids) | Q(curso__isnull=True)
    ).select_related('curso', 'categoria')

    # Obtener también Recursos Académicos (Legacy/Profesor view)
    from academico.models import RecursoAcademico
    recursos_qs = RecursoAcademico.objects.filter(
        curso__id__in=mis_cursos_ids
    ).select_related('curso', 'profesor', 'asignatura')

    # Combinar ambas listas
    # Normalizamos atributos comunes para el template
    lista_material = []
    
    from django.urls import reverse

    for doc in qs:
        lista_material.append({
            'tipo_obj': 'documento',
            'id': doc.id,
            'titulo': doc.titulo,
            'descripcion': doc.descripcion,
            'archivo_url': doc.archivo.url if doc.archivo else '',
            'url_descarga': reverse('documentos:descargar_documento', args=[doc.id]),
            'curso': doc.curso,
            'asignatura': None, # Documento no tiene asignatura directa
            'fecha': doc.fecha_creacion,
            'autor': doc.creado_por.get_full_name(),
            'tamaño': doc.tamaño_formateado,
            'tipo': doc.tipo,
            'icon': 'bi-file-earmark-text', # Icono por defecto (se pisa en template si hay logica visual)
            'categoria': doc.categoria.nombre
        })

    for rec in recursos_qs:
        # Calcular tamaño si es posible, o dejar vacío
        size_str = ""
        ext = 'file'
        try:
             if rec.archivo:
                s = rec.archivo.size
                if s < 1024: size_str = f"{s} B"
                elif s < 1024*1024: size_str = f"{s/1024:.1f} KB"
                else: size_str = f"{s/(1024*1024):.1f} MB"
                
                # Inferir extensión para el icono
                import os
                _, ext_raw = os.path.splitext(rec.archivo.name)
                ext = ext_raw.lower().replace('.', '')
        except: pass

        lista_material.append({
            'tipo_obj': 'recurso',
            'id': rec.id,
            'titulo': rec.titulo,
            'descripcion': rec.descripcion,
            'archivo_url': rec.archivo.url if rec.archivo else '',
            'url_descarga': reverse('academico:descargar_recurso', args=[rec.id]),
            'curso': rec.curso,
            'asignatura': rec.asignatura,
            'fecha': rec.creado,
            'autor': rec.profesor.get_full_name(),
            'tamaño': size_str,
            'tipo': ext, # Usamos la extensión inferida como tipo
            'icon': 'bi-journal-bookmark',
            'categoria': 'Recurso de Asignatura'
        })
    
    # Ordenar por fecha descendente
    lista_material.sort(key=lambda x: x['fecha'], reverse=True)

    context = {
        'documentos': lista_material, # El template itera sobre 'documentos'
    }
    return render(request, 'documentos/material_estudio.html', context)
