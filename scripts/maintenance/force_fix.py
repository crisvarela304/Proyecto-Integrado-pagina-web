
import os

content_mis_estudiantes = """{% extends "base.html" %}
{% load static %}
{% load dict_extras %}
{% block title %}{% if modo_calificaciones %}Calificar Estudiantes{% else %}Mis Estudiantes{% endif %}{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col-12">
            <div class="card border-0 shadow-sm bg-light">
                <div class="card-body">
                    <h4 class="mb-0">{% if modo_calificaciones %}Calificar Estudiantes{% else %}Estudiantes a Cargo{% endif %}</h4>
                    <p class="text-muted mb-0">{% if modo_calificaciones %}Selecciona un estudiante para registrar sus notas.{% else %}Listado filtrable por curso y búsqueda.{% endif %}</p>
                </div>
            </div>
        </div>
    </div>

    <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
            <form class="row g-3">
                <div class="col-md-4">
                    <label class="form-label">Curso</label>
                    <select name="curso" class="form-select">
                        <option value="">Todos</option>
                        {% for curso in cursos_profesor %}
                            <option value="{{ curso.id }}" {% if curso_seleccionado == curso.id|stringformat:"s" %}selected{% endif %}>
                                {{ curso }}
                            </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Buscar</label>
                    <input type="text" name="busqueda" class="form-control" placeholder="Nombre, apellido o RUT" value="{{ busqueda }}">
                </div>
                <div class="col-md-4 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary me-2">
                        <i class="bi bi-search"></i> Buscar
                    </button>
                    <a href="{% if modo_calificaciones %}{% url 'academico:lista_calificaciones_profesor' %}{% else %}{% url 'academico:mis_estudiantes_profesor' %}{% endif %}" class="btn btn-outline-secondary">
                        Limpiar
                    </a>
                </div>
            </form>
        </div>
    </div>

    <div class="card border-0 shadow-sm">
        <div class="card-body">
            {% if page_obj %}
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>RUT</th>
                            <th>Curso</th>
                            <th>Teléfono estudiante</th>
                            <th>Teléfono apoderado</th>
                            <th>Estado</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for inscripcion in page_obj %}
                        <tr>
                            {% with perfil=perfiles_estudiantes|get_item:inscripcion.estudiante.id %}
                            <td>{{ inscripcion.estudiante.get_full_name|default:inscripcion.estudiante.username }}</td>
                            <td>
                                {% if perfil %}
                                    {{ perfil.rut }}
                                {% else %}
                                    Sin registro
                                {% endif %}
                            </td>
                            <td>{{ inscripcion.curso }}</td>
                            <td>
                                {% if perfil and perfil.telefono_estudiante %}
                                    {{ perfil.telefono_estudiante }}
                                {% else %}
                                    Sin registro
                                {% endif %}
                            </td>
                            <td>
                                {% if perfil and perfil.telefono_apoderado %}
                                    {{ perfil.telefono_apoderado }}
                                {% else %}
                                    Sin registro
                                {% endif %}
                            </td>
                            <td>
                                <span class="badge bg-success">{{ inscripcion.get_estado_display }}</span>
                            </td>
                            <td class="text-end">
                                {% if modo_calificaciones %}
                                <a href="{% url 'academico:gestionar_calificaciones' inscripcion.estudiante.id %}" class="btn btn-sm btn-primary">
                                    <i class="bi bi-pencil-square me-1"></i> Calificar
                                </a>
                                {% else %}
                                <a href="{% url 'academico:detalle_estudiante' inscripcion.estudiante.id %}" class="btn btn-sm btn-outline-info">
                                    <i class="bi bi-person-badge me-1"></i> Ver Perfil
                                </a>
                                {% endif %}
                            </td>
                            {% endwith %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="d-flex justify-content-between align-items-center">
                <div>
                    Mostrando {{ page_obj.start_index }} - {{ page_obj.end_index }} de {{ page_obj.paginator.count }}
                </div>
                <div>
                    {% if page_obj.has_previous %}
                        <a href="?page={{ page_obj.previous_page_number }}&busqueda={{ busqueda }}&curso={{ curso_seleccionado }}" class="btn btn-outline-secondary btn-sm">Anterior</a>
                    {% endif %}
                    {% if page_obj.has_next %}
                        <a href="?page={{ page_obj.next_page_number }}&busqueda={{ busqueda }}&curso={{ curso_seleccionado }}" class="btn btn-outline-secondary btn-sm">Siguiente</a>
                    {% endif %}
                </div>
            </div>
            {% else %}
                <div class="text-center text-muted py-4">
                    <i class="bi bi-people fs-1"></i>
                    <p class="mb-0">No se encontraron estudiantes</p>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}"""

path = 'apps/academico/templates/academico/profesor_mis_estudiantes.html'
with open(path, 'w', encoding='utf-8') as f:
    f.write(content_mis_estudiantes)
print(f"Overwritten {path}")
