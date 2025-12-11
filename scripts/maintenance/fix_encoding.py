
import os

files = {
    'apps/core/templates/core/contacto.html': """{% extends "base.html" %}
{% load static %}

{% block title %}Contacto{% endblock %}

{% block content %}
<!-- Hero Section -->
<div class="bg-light py-5 mb-5">
    <div class="container">
        <div class="row justify-content-center text-center">
            <div class="col-lg-8">
                <h1 class="display-4 fw-bold mb-3">Contáctanos</h1>
                <p class="lead text-muted mb-0">Estamos aquí para responder tus dudas y consultas.</p>
            </div>
        </div>
    </div>
</div>

<div class="container pb-5">
    <div class="row g-5">
        <!-- Información de Contacto -->
        <div class="col-lg-5">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body p-4">
                    <h3 class="fw-bold mb-4">Información</h3>
                    
                    <div class="d-flex mb-4">
                        <div class="flex-shrink-0">
                            <div class="bg-primary bg-opacity-10 p-3 rounded-circle text-primary">
                                <i class="bi bi-geo-alt fs-4"></i>
                            </div>
                        </div>
                        <div class="ms-3">
                            <h5 class="fw-bold mb-1">Dirección</h5>
                            <p class="text-muted mb-0">Av. La Paz 450, Hualqui, Región del Biobío</p>
                        </div>
                    </div>

                    <div class="d-flex mb-4">
                        <div class="flex-shrink-0">
                            <div class="bg-success bg-opacity-10 p-3 rounded-circle text-success">
                                <i class="bi bi-telephone fs-4"></i>
                            </div>
                        </div>
                        <div class="ms-3">
                            <h5 class="fw-bold mb-1">Teléfono</h5>
                            <p class="text-muted mb-0">+56 41 278 1234</p>
                        </div>
                    </div>

                    <div class="d-flex mb-4">
                        <div class="flex-shrink-0">
                            <div class="bg-info bg-opacity-10 p-3 rounded-circle text-info">
                                <i class="bi bi-envelope fs-4"></i>
                            </div>
                        </div>
                        <div class="ms-3">
                            <h5 class="fw-bold mb-1">Email</h5>
                            <p class="text-muted mb-0">contacto@liceojuanbautista.cl</p>
                        </div>
                    </div>
                    
                    <hr class="my-4">
                    
                    <h5 class="fw-bold mb-3">Horario de Atención</h5>
                    <ul class="list-unstyled text-muted">
                        <li class="mb-2 d-flex justify-content-between">
                            <span>Lunes - Viernes:</span>
                            <span class="fw-bold text-dark">08:00 - 17:00</span>
                        </li>
                        <li class="d-flex justify-content-between">
                            <span>Sábado - Domingo:</span>
                            <span class="fw-bold text-dark">Cerrado</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Formulario -->
        <div class="col-lg-7">
            <div class="card border-0 shadow-sm">
                <div class="card-body p-4">
                    <h3 class="fw-bold mb-4">Envíanos un mensaje</h3>
                    <form method="post" class="needs-validation" novalidate>
                        {% csrf_token %}
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label for="nombre" class="form-label">Nombre completo</label>
                                <input type="text" class="form-control" id="nombre" name="nombre" required>
                                <div class="invalid-feedback">
                                    Por favor ingresa tu nombre.
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                                <div class="invalid-feedback">
                                    Por favor ingresa un email válido.
                                </div>
                            </div>
                            <div class="col-12">
                                <label for="asunto" class="form-label">Asunto</label>
                                <input type="text" class="form-control" id="asunto" name="asunto" required>
                                <div class="invalid-feedback">
                                    Por favor ingresa el asunto.
                                </div>
                            </div>
                            <div class="col-12">
                                <label for="mensaje" class="form-label">Mensaje</label>
                                <textarea class="form-control" id="mensaje" name="mensaje" rows="5" required></textarea>
                                <div class="invalid-feedback">
                                    Por favor ingresa tu mensaje.
                                </div>
                            </div>
                            <div class="col-12">
                                <button type="submit" class="btn btn-primary btn-lg w-100">
                                    <i class="bi bi-send me-2"></i>Enviar Mensaje
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Bootstrap validation script
    (function () {
        'use strict'
        var forms = document.querySelectorAll('.needs-validation')
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    }
                    form.classList.add('was-validated')
                }, false)
            })
    })()
</script>
{% endblock %}""",
    'apps/core/templates/core/reglamentos.html': """{% extends "base.html" %}

{% block title %}Reglamentos - Liceo Juan Bautista{% endblock %}

{% block content %}
<div class="container my-5">
    <h1 class="mb-4">Reglamentos</h1>
    <p class="lead">Documentos institucionales y normativas vigentes.</p>
    
    <div class="alert alert-info">
        <i class="fas fa-info-circle me-2"></i>
        Sección en construcción. Los reglamentos estarán disponibles pronto.
    </div>
</div>
{% endblock %}"""
}

for path, content in files.items():
    abs_path = os.path.abspath(path)
    print(f"Writing {abs_path}...")
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done.")
