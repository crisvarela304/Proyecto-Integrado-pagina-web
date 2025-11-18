from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import (
    Documento, CategoriaDocumento, HistorialDescargas, 
    TipoExamen, Examen, PreguntaExamen, ComunicadoPadres
)
from .forms import DocumentoForm
from usuarios.models import PerfilUsuario
import mimetypes
import os

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
    
    # Contexto
    categorias = CategoriaDocumento.objects.filter(activa=True)
    tipos_documento = dict(Documento.TIPO_CHOICES)
    tipos_visibilidad = dict(Documento.VISIBILIDAD_CHOICES)
    
    return render(request, "documentos/documentos_list.html", {
        "page_obj": page_obj,
        "query": q,
        "categoria_filtro": categoria,
        "tipo_filtro": tipo,
        "visibilidad_filtro": visibilidad,
        "categorias": categorias,
        "tipos_documento": tipos_documento,
        "tipos_visibilidad": tipos_visibilidad
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

@login_required
def examenes_calendario(request):
    """Calendario de exámenes"""
    qs = Examen.objects.filter(activo=True)
    
    # Filtros
    curso_id = request.GET.get('curso', '').strip()
    asignatura_id = request.GET.get('asignatura', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    
    # Aplicar filtros
    if curso_id:
        qs = qs.filter(curso_id=curso_id)
    
    if asignatura_id:
        qs = qs.filter(asignatura_id=asignatura_id)
    
    if fecha_desde:
        qs = qs.filter(fecha_aplicacion__gte=fecha_desde)
    
    if fecha_hasta:
        qs = qs.filter(fecha_aplicacion__lte=fecha_hasta)
    
    # Filtrar por permisos del usuario
    perfil = getattr(request.user, 'perfil', None)
    if perfil:
        if perfil.tipo_usuario == 'estudiante':
            # Solo exámenes de los cursos donde está inscrito
            from academico.models import InscripcionCurso
            mis_cursos = InscripcionCurso.objects.filter(
                estudiante=request.user, 
                estado='activo'
            ).values_list('curso_id', flat=True)
            qs = qs.filter(curso_id__in=mis_cursos)
        elif perfil.tipo_usuario == 'profesor':
            # Solo exámenes que él creó
            qs = qs.filter(profesor=request.user)
    
    qs = qs.order_by('fecha_aplicacion', 'hora_inicio')
    
    # Importar modelos necesarios para filtros
    from academico.models import Curso, Asignatura
    
    return render(request, "documentos/examenes_calendario.html", {
        "examenes": qs,
        "cursos": Curso.objects.all(),
        "asignaturas": Asignatura.objects.all(),
        "filtros": {
            "curso": curso_id,
            "asignatura": asignatura_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }
    })

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
    if not request.user.is_staff:
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
    
    return render(request, "documentos/subir_documento.html", {"form": form})
