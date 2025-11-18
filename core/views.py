from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from comunicacion.models import Noticia

def home(request):
    noticias_destacadas = Noticia.objects.filter(es_publica=True, destacado=True).order_by('-creado')[:3]
    context = {
        'noticias_destacadas': noticias_destacadas
    }
    return render(request, 'core/home.html', context)

def contacto(request):
    """Página de contacto"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        email = request.POST.get('email', '')
        asunto = request.POST.get('asunto', '')
        mensaje = request.POST.get('mensaje', '')
        
        # Simular envío de correo (en desarrollo)
        messages.success(request, '¡Mensaje enviado! Te contactaremos pronto.')
        return render(request, 'core/contacto.html')
    
    return render(request, 'core/contacto.html')

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
                        <h1 class="display-1 text-muted">404</h1>
                        <h2 class="mb-3">Página no encontrada</h2>
                        <p class="lead text-muted mb-4">
                            La página que buscas no existe.
                        </p>
                        <div class="d-flex justify-content-center gap-3">
                            <a href="/" class="btn btn-primary">
                                Volver al Inicio
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    return HttpResponse(html, status=404)
