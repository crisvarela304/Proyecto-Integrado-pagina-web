"""
Vistas de la aplicación core.
Solución definitiva sin templates problemáticos.
"""

from django.http import HttpResponse, Http404
from django.conf import settings
from comunicacion.models import Noticia

def home(request):
    """
    Vista de inicio que genera HTML directamente para evitar problemas de codificación.
    """
    # Obtener noticias destacadas
    noticias_destacadas = Noticia.objects.filter(es_publica=True, destacado=True).order_by('-creado')[:3]
    
    # Crear HTML sin usar templates
    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Inicio - Liceo Juan Bautista de Hualqui</title>
    
    <!-- Bootstrap 5 CSS desde CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome desde CDN -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        body { background-color: #f8f9fa; }
        .hero-section { background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 60px 0; }
        .news-card { transition: transform 0.3s ease; }
        .news-card:hover { transform: translateY(-5px); }
        .card { border-radius: 12px; }
        .navbar-brand { font-weight: bold; }
        .btn { border-radius: 8px; }
    </style>
</head>
<body>
    <!-- Navegación -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-school me-2"></i>Liceo Juan Bautista de Hualqui
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/">
                            <i class="fas fa-home me-1"></i>Inicio
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/noticias/">
                            <i class="fas fa-newspaper me-1"></i>Noticias
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/usuarios/login/">
                            <i class="fas fa-sign-in-alt me-1"></i>Iniciar Sesión
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/admin/">
                            <i class="fas fa-cog me-1"></i>Admin
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section text-center">
        <div class="container">
            <div class="row">
                <div class="col-lg-8 mx-auto">
                    <h1 class="display-4 fw-bold mb-3">
                        <i class="fas fa-graduation-cap me-3"></i>
                        Liceo Juan Bautista de Hualqui
                    </h1>
                    <p class="lead mb-4">
                        Portal institucional moderno para mejorar la comunicación entre el establecimiento, 
                        apoderados y estudiantes.
                    </p>
                    <div class="d-flex justify-content-center gap-3">
                        <a href="/noticias/" class="btn btn-light btn-lg">
                            <i class="fas fa-newspaper me-2"></i>Ver Noticias
                        </a>
                        <a href="/usuarios/login/" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contenido Principal -->
    <div class="container my-5">
        <div class="row">
            <div class="col-lg-8">
                <h2 class="mb-4">
                    <i class="fas fa-star text-warning me-2"></i>
                    Noticias Destacadas
                </h2>'''
    
    # Agregar noticias destacadas
    if noticias_destacadas:
        html += '<div class="row g-3">'
        for noticia in noticias_destacadas:
            html += f'''
            <div class="col-md-6">
                <div class="card news-card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge bg-warning text-dark">
                                <i class="fas fa-star"></i> Destacada
                            </span>
                            <small class="text-muted">{noticia.creado.strftime("%d/%m/%Y")}</small>
                        </div>
                        <h5 class="card-title">{noticia.titulo}</h5>
                        <p class="card-text text-muted">{noticia.bajada}</p>
                        <div class="mt-auto">
                            <a href="/noticias/{noticia.pk}/" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-eye me-1"></i>Leer más
                            </a>
                        </div>
                    </div>
                </div>
            </div>'''
        html += '</div>'
    else:
        html += '''<div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No hay noticias destacadas disponibles.
                </div>'''
    
    html += '''
                <div class="text-center mt-4">
                    <a href="/noticias/" class="btn btn-primary btn-lg">
                        <i class="fas fa-newspaper me-2"></i>Explorar Centro de Noticias
                    </a>
                </div>
            </div>
            
            <!-- Panel Lateral -->
            <div class="col-lg-4">
                <h3 class="mb-4">
                    <i class="fas fa-bolt text-warning me-2"></i>
                    Acceso Rápido
                </h3>
                
                <div class="list-group mb-4">
                    <a href="/noticias/" class="list-group-item list-group-item-action border-0 shadow-sm mb-2">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-newspaper text-primary fa-lg me-3"></i>
                            <div>
                                <h6 class="mb-1">Centro de Noticias</h6>
                                <small class="text-muted">Mantente informado</small>
                            </div>
                        </div>
                    </a>
                    
                    <a href="/usuarios/login/" class="list-group-item list-group-item-action border-0 shadow-sm mb-2">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-sign-in-alt text-success fa-lg me-3"></i>
                            <div>
                                <h6 class="mb-1">Iniciar Sesión</h6>
                                <small class="text-muted">Accede a tu cuenta</small>
                            </div>
                        </div>
                    </a>
                    
                    <a href="/admin/" class="list-group-item list-group-item-action border-0 shadow-sm mb-2">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-cog text-info fa-lg me-3"></i>
                            <div>
                                <h6 class="mb-1">Administración</h6>
                                <small class="text-muted">Panel de control</small>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
    
    return HttpResponse(html)

def error_404(request, exception):
    """
    Manejador personalizado para errores 404.
    """
    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Página no encontrada</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container text-center mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card border-0 shadow">
                    <div class="card-body py-5">
                        <i class="fas fa-exclamation-triangle text-warning" style="font-size: 4rem;"></i>
                        <h1 class="display-1 text-muted">404</h1>
                        <h2 class="mb-3">Página no encontrada</h2>
                        <p class="lead text-muted mb-4">
                            La página que buscas no existe.
                        </p>
                        <div class="d-flex justify-content-center gap-3">
                            <a href="/" class="btn btn-primary">
                                <i class="fas fa-home me-2"></i>Volver al Inicio
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    response = HttpResponse(html, status=404)
    return response
