import os

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/mis_asistencias.html'

correct_content = """{% extends "base.html" %}
{% load static %}
{% block title %}Mis Asistencias{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Cabecera -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <h2 class="mb-1">Mis Asistencias</h2>
                            <p class="text-muted mb-0">Historial de asistencia y presencia en clases</p>
                        </div>
                        <div>
                            <a href="{% url 'usuarios:panel' %}" class="btn btn-outline-primary">
                                <i class="bi bi-arrow-left"></i> Volver al Panel
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Filtros -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-body">
                    <form method="get" class="row g-3 align-items-end">
                        <div class="col-md-5">
                            <label class="form-label">Filtrar por mes</label>
                            <input type="month" name="mes" class="form-control"
                                value="{{ mes_seleccionado|default:'' }}">
                        </div>
                        <div class="col-md-5">
                            <label class="form-label">Filtrar por Estado</label>
                            <select name="estado" class="form-select">
                                <option value="">Todos los estados</option>
                                <option value="presente" {% if estado_seleccionado == 'presente' %}selected{% endif %}>Presente</option>
                                <option value="ausente" {% if estado_seleccionado == 'ausente' %}selected{% endif %}>Ausente</option>
                                <option value="tardanza" {% if estado_seleccionado == 'tardanza' %}selected{% endif %}>Tardanza</option>
                                <option value="justificado" {% if estado_seleccionado == 'justificado' %}selected{% endif %}>Justificado</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-funnel"></i> Filtrar
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Estadísticas de asistencia -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card text-white bg-success">
                <div class="card-body text-center">
                    <i class="bi bi-check-circle fs-1 mb-2"></i>
                    <h3 class="mb-0">{{ estadisticas.presentes }}</h3>
                    <small>Presentes</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-danger">
                <div class="card-body text-center">
                    <i class="bi bi-x-circle fs-1 mb-2"></i>
                    <h3 class="mb-0">{{ estadisticas.ausentes }}</h3>
                    <small>Ausentes</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-warning">
                <div class="card-body text-center">
                    <i class="bi bi-clock fs-1 mb-2"></i>
                    <h3 class="mb-0">{{ estadisticas.tardanzas }}</h3>
                    <small>Tardanzas</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-info">
                <div class="card-body text-center">
                    <i class="bi bi-shield-check fs-1 mb-2"></i>
                    <h3 class="mb-0">{{ estadisticas.justificadas }}</h3>
                    <small>Justificadas</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Gráfico de asistencia -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-pie-chart me-2"></i>Distribución de Asistencia
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="mb-3">
                                <div class="progress mx-auto" style="width: 80px; height: 80px;">
                                    <div class="progress-bar bg-success" role="progressbar"
                                        style="width: {% if estadisticas.presentes %}{{ estadisticas.presentes|floatformat:0 }}%{% else %}0%{% endif %}">
                                    </div>
                                </div>
                            </div>
                            <h5 class="text-success">{{ estadisticas.presentes }}</h5>
                            <small>Presentes</small>
                        </div>
                        <div class="col-6">
                            <div class="mb-3">
                                <div class="progress mx-auto" style="width: 80px; height: 80px;">
                                    <div class="progress-bar bg-danger" role="progressbar"
                                        style="width: {% if estadisticas.ausentes %}{{ estadisticas.ausentes|floatformat:0 }}%{% else %}0%{% endif %}">
                                    </div>
                                </div>
                            </div>
                            <h5 class="text-danger">{{ estadisticas.ausentes }}</h5>
                            <small>Ausentes</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-bar-chart me-2"></i>Porcentaje de Asistencia
                    </h5>
                </div>
                <div class="card-body">
                    {% with total=estadisticas.presentes|add:estadisticas.ausentes %}
                    {% if total > 0 %}
                    {% widthratio estadisticas.presentes total 100 as porcentaje %}
                    <div class="text-center">
                        <h2 class="text-primary">{{ porcentaje|default:0|floatformat:1 }}%</h2>
                        <div class="progress mb-3" style="height: 20px;">
                            <div class="progress-bar bg-success" role="progressbar"
                                style="width: {{ porcentaje|default:0 }}%"></div>
                        </div>
                        <p class="text-muted">Asistencia total</p>
                    </div>
                    {% else %}
                    <div class="text-center">
                        <h2 class="text-muted">--</h2>
                        <p class="text-muted">Sin datos de asistencia</p>
                    </div>
                    {% endif %}
                    {% endwith %}
                </div>
            </div>
        </div>
    </div>

    <!-- Tabla de asistencias -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-table me-2"></i>Detalle de Asistencias
                    </h5>
                </div>
                <div class="card-body">
                    {% if asistencias %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Fecha</th>
                                    <th>Curso</th>
                                    <th>Estado</th>
                                    <th>Observaciones</th>
                                    <th>Registrado por</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for asistencia in asistencias %}
                                <tr>
                                    <td>{{ asistencia.fecha|date:"d/m/Y" }}</td>
                                    <td>{{ asistencia.curso }}</td>
                                    <td>
                                        {% if asistencia.estado == 'presente' %}
                                        <span class="badge bg-success">
                                            <i class="bi bi-check-circle me-1"></i>Presente
                                        </span>
                                        {% elif asistencia.estado == 'ausente' %}
                                        <span class="badge bg-danger">
                                            <i class="bi bi-x-circle me-1"></i>Ausente
                                        </span>
                                        {% elif asistencia.estado == 'tardanza' %}
                                        <span class="badge bg-warning">
                                            <i class="bi bi-clock me-1"></i>Tardanza
                                        </span>
                                        {% elif asistencia.estado == 'justificado' %}
                                        <span class="badge bg-info">
                                            <i class="bi bi-shield-check me-1"></i>Justificado
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td>{{ asistencia.observacion|default:"Sin observaciones" }}</td>
                                    <td>{{ asistencia.registrado_por.get_full_name|default:asistencia.registrado_por.username }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="text-center py-5">
                        <i class="bi bi-calendar-x display-1 text-muted"></i>
                        <h4 class="mt-3 text-muted">No hay asistencias registradas</h4>
                        <p class="text-muted">No se encontraron registros de asistencia para el período seleccionado.
                        </p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Leyenda de estados -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="card bg-light">
                <div class="card-body">
                    <h6 class="card-title">Estados de Asistencia</h6>
                    <div class="row">
                        <div class="col-md-3">
                            <span class="badge bg-success fs-6">Presente</span> Estudiante asistió a clase
                        </div>
                        <div class="col-md-3">
                            <span class="badge bg-danger fs-6">Ausente</span> Estudiante no asistió
                        </div>
                        <div class="col-md-3">
                            <span class="badge bg-warning fs-6">Tardanza</span> Llegó después de la hora
                        </div>
                        <div class="col-md-3">
                            <span class="badge bg-info fs-6">Justificado</span> Ausencia justificada
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

print(f"Removing {file_path}")
try:
    if os.path.exists(file_path):
        os.remove(file_path)
        print("Removed existing file.")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(correct_content)
    print("Wrote new content.")
    
    # Verification
    with open(file_path, 'r', encoding='utf-8') as f:
        read_back = f.read()
        if "estado_seleccionado == 'presente'" in read_back:
            print("VERIFICATION SUCCESS: Spaces found.")
        else:
            print("VERIFICATION FAILED: Spaces NOT found.")
            
except Exception as e:
    print(f"Error: {e}")
