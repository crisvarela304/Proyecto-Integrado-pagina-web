from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Noticia, CategoriaNoticia

def noticias_list(request):
    # Obtener parámetros de búsqueda y filtrado
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    orden = request.GET.get('orden', 'recientes')
    
    # Query base
    # Query base optimizada
    qs = Noticia.objects.filter(es_publica=True).select_related('autor')
    
    # Aplicar filtros
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) | 
            Q(bajada__icontains=q) | 
            Q(cuerpo__icontains=q)
        )
    
    if categoria:
        qs = qs.filter(categoria=categoria)
    
    # Aplicar ordenamiento
    if orden == 'visitas':
        qs = qs.order_by('-visitas', '-creado')
    elif orden == 'categoria':
        qs = qs.order_by('categoria', '-creado')
    else:  # recientes por defecto
        qs = qs.order_by('-creado')
    
    # Paginación
    paginator = Paginator(qs, 8)  # 8 noticias por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Obtener categorías para el filtro
    categorias = CategoriaNoticia.objects.filter(activa=True)
    
    template_name = "comunicacion/noticias_list.html"
    if request.htmx:
        template_name = "comunicacion/_noticias_list_partial.html"

    return render(request, template_name, {
        "page_obj": page_obj,
        "query": q,
        "categoria_filtro": categoria,
        "orden_actual": orden,
        "categorias": categorias
    })

def noticia_detalle(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk, es_publica=True)
    
    # Incrementar contador de visitas
    noticia.increment_visits()
    
    # Obtener noticias relacionadas (misma categoría)
    noticias_relacionadas = Noticia.objects.filter(
        categoria=noticia.categoria,
        es_publica=True
    ).exclude(pk=noticia.pk).order_by('-creado')[:3]
    
    # Obtener últimos noticias destacadas
    destacadas = Noticia.objects.filter(
        es_publica=True,
        destacado=True
    ).exclude(pk=noticia.pk).order_by('-creado')[:4]
    
    return render(request, "comunicacion/noticia_detalle.html", {
        "noticia": noticia,
        "noticias_relacionadas": noticias_relacionadas,
        "destacadas": destacadas
    })

@login_required
def noticias_privadas(request):
    """Vista para mostrar noticias privadas en el panel"""
    qs = Noticia.objects.all().order_by('-creado')
    return render(request, "comunicacion/noticias_privadas.html", {"noticias": qs})

@login_required
def estadisticas_noticias(request):
    """Vista para estadísticas de noticias (solo para administradores)"""
    if not request.user.is_staff:
        return render(request, "core/404.html", status=404)
    
    total_noticias = Noticia.objects.count()
    noticias_por_categoria = Noticia.objects.values('categoria').annotate(
        total=Count('categoria')
    ).order_by('-total')
    
    noticias_mas_vistas = Noticia.objects.order_by('-visitas')[:10]
    
    return render(request, "comunicacion/estadisticas.html", {
        "total_noticias": total_noticias,
        "noticias_por_categoria": noticias_por_categoria,
        "noticias_mas_vistas": noticias_mas_vistas
    })

# --- Vistas de Gestión (Frontend) ---
from .forms import NoticiaForm

@login_required
def gestion_noticias(request):
    """Vista para listar y gestionar noticias (admin/staff)"""
    # Verificar permisos (staff o administrativo/directivo)
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        messages.error(request, "No tienes permisos para gestionar noticias.")
        return redirect('home')
        
    noticias = Noticia.objects.all().order_by('-creado')
    return render(request, "comunicacion/gestion_noticias.html", {"noticias": noticias})

@login_required
def crear_noticia(request):
    """Crear nueva noticia desde frontend"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        messages.error(request, "No tienes permisos para crear noticias.")
        return redirect('home')

    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            messages.success(request, 'Noticia publicada exitosamente.')
            return redirect('administrativo:dashboard')
    else:
        form = NoticiaForm()
    
    return render(request, 'comunicacion/form_noticia.html', {'form': form})

@login_required
def editar_noticia(request, pk):
    """Editar noticia existente"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        return redirect('home')

    noticia = get_object_or_404(Noticia, pk=pk)
    
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada correctamente.')
            return redirect('comunicacion:gestion_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    
    return render(request, 'comunicacion/form_noticia.html', {'form': form})

@login_required
def eliminar_noticia(request, pk):
    """Eliminar noticia"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        return redirect('home')

    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada.')
    
    return redirect('comunicacion:gestion_noticias')

