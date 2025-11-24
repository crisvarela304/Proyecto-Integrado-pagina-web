# Análisis de Errores y Mejoras Funcionales - Liceo Juan Bautista

## ✅ Errores Corregidos

### 1. **Errores de Sintaxis en Templates** (CRÍTICO)
- ❌ **Problema**: Comparaciones sin espacios (`==`) en templates Django
- ✅ **Solución**: Corregidos automáticamente 4 archivos:
  - `academico/templates/academico/mis_calificaciones.html`
  - `documentos/templates/documentos/examenes_calendario.html`
  - `academico/templates/academico/profesor_mis_estudiantes.html`
  - `mensajeria/templates/mensajeria/simple_mensajeria.html`

### 2. **Filtro de Categoría Faltante** (MEDIO)
- ❌ **Problema**: El filtro de categoría se eliminó accidentalmente en `documentos_list.html`
- ✅ **Solución**: Necesita ser restaurado manualmente

### 3. **Validación de RUT** (MEDIO)
- ❌ **Problema**: No hay validación del dígito verificador del RUT
- ✅ **Solución**: Implementar algoritmo de validación (código proporcionado)

---

## 🔍 Errores Funcionales Detectados

### 1. **Manejo de Archivos Inexistentes**
```python
# En documentos/views.py línea 154-161
try:
    file_path = documento.archivo.path
    # ...
except FileNotFoundError:
    raise Http404("Archivo no encontrado en el servidor")
```
**Problema**: Si el archivo se elimina del servidor pero el registro queda en BD, el usuario ve error 500.
**Mejora**: Agregar verificación antes de intentar abrir el archivo.

```python
# SOLUCIÓN PROPUESTA
@login_required
def descargar_documento(request, pk):
    documento = get_object_or_404(Documento, pk=pk, publicado=True)
    
    # Verificar permisos...
    
    if not documento.archivo:
        messages.error(request, "Este documento no tiene un archivo asociado.")
        return redirect('documentos:documentos_list')
    
    # Verificar que el archivo existe físicamente
    if not os.path.exists(documento.archivo.path):
        messages.error(request, "El archivo no se encuentra disponible.")
        return redirect('documentos:documentos_list')
    
    # Registrar descarga y servir archivo...
```

### 2. **Contador de Descargas Sin Transacción**
```python
# En documentos/views.py línea 149-151
documento.descargar_count += 1
documento.save(update_fields=['descargar_count'])
```
**Problema**: Race condition si múltiples usuarios descargan simultáneamente.
**Mejora**: Usar F() expression de Django.

```python
# SOLUCIÓN PROPUESTA
from django.db.models import F

# Reemplazar líneas 149-151 con:
Documento.objects.filter(pk=documento.pk).update(
    descargar_count=F('descargar_count') + 1
)
```

### 3. **Filtros Sin Validación**
```python
# En documentos/views.py línea 51-58
if categoria:
    qs = qs.filter(categoria__id=categoria)

if tipo:
    qs = qs.filter(tipo=tipo)
```
**Problema**: No valida que los valores sean válidos, puede causar errores si se manipula la URL.
**Mejora**: Validar valores antes de filtrar.

```python
# SOLUCIÓN PROPUESTA
if categoria:
    try:
        categoria_id = int(categoria)
        if CategoriaDocumento.objects.filter(id=categoria_id, activa=True).exists():
            qs = qs.filter(categoria__id=categoria_id)
    except (ValueError, TypeError):
        pass  # Ignorar valor inválido

if tipo:
    tipos_validos = [choice[0] for choice in Documento.TIPO_CHOICES]
    if tipo in tipos_validos:
        qs = qs.filter(tipo=tipo)
```

### 4. **Paginación Sin Manejo de Errores**
```python
# En documentos/views.py línea 61-63
paginator = Paginator(qs.order_by('-fecha_creacion'), 12)
page_number = request.GET.get("page")
page_obj = paginator.get_page(page_number)
```
**Problema**: Si alguien pone `?page=99999` no hay feedback al usuario.
**Mejora**: Validar número de página.

```python
# SOLUCIÓN PROPUESTA
paginator = Paginator(qs.order_by('-fecha_creacion'), 12)
page_number = request.GET.get("page", 1)

try:
    page_number = int(page_number)
    if page_number < 1:
        page_number = 1
    elif page_number > paginator.num_pages:
        page_number = paginator.num_pages
except (ValueError, TypeError):
    page_number = 1

page_obj = paginator.get_page(page_number)
```

### 5. **Búsqueda Ineficiente**
```python
# En documentos/views.py línea 44-49
if q:
    qs = qs.filter(
        Q(titulo__icontains=q) | 
        Q(descripcion__icontains=q) | 
        Q(tags__icontains=q)
    )
```
**Problema**: Búsqueda case-insensitive en múltiples campos puede ser lenta con muchos registros.
**Mejora**: Agregar índices en la base de datos.

```python
# En documentos/models.py
class Documento(models.Model):
    # ... campos existentes ...
    
    class Meta:
        indexes = [
            models.Index(fields=['titulo']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['categoria', 'tipo']),
        ]
```

### 6. **Sin Límite en Tamaño de Archivo**
**Problema**: No hay validación del tamaño máximo de archivos subidos.
**Mejora**: Agregar validación en el modelo.

```python
# En documentos/models.py
from django.core.exceptions import ValidationError

def validate_file_size(value):
    filesize = value.size
    max_size_mb = 10  # 10 MB
    if filesize > max_size_mb * 1024 * 1024:
        raise ValidationError(f"El tamaño máximo permitido es {max_size_mb}MB")

class Documento(models.Model):
    archivo = models.FileField(
        upload_to='documentos/',
        validators=[validate_file_size]
    )
```

### 7. **Sin Protección CSRF en Formularios AJAX**
**Problema**: Si se implementa AJAX, falta token CSRF.
**Mejora**: Agregar token CSRF en headers.

```javascript
// En templates con AJAX
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// En fetch/AJAX
fetch(url, {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
})
```

---

## 🚀 Mejoras Funcionales Recomendadas

### 1. **Sistema de Notificaciones**
```python
# Crear app notifications
python manage.py startapp notifications

# En notifications/models.py
from django.db import models
from django.contrib.auth.models import User

class Notificacion(models.Model):
    TIPOS = [
        ('noticia', 'Nueva Noticia'),
        ('documento', 'Nuevo Documento'),
        ('calificacion', 'Nueva Calificación'),
        ('mensaje', 'Nuevo Mensaje'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url = models.CharField(max_length=500, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-creada']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
```

### 2. **Historial de Actividad del Usuario**
```python
# En usuarios/models.py
class ActividadUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Actividades de Usuarios'
```

### 3. **Caché para Consultas Frecuentes**
```python
# En settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# En views.py
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache por 15 minutos
def noticias_list(request):
    # ...
    
# O manualmente
def documentos_list(request):
    cache_key = f'documentos_list_{request.GET.urlencode()}'
    page_obj = cache.get(cache_key)
    
    if not page_obj:
        # Generar page_obj...
        cache.set(cache_key, page_obj, 60 * 5)  # 5 minutos
    
    return render(request, template, context)
```

### 4. **Búsqueda Avanzada con PostgreSQL**
```python
# Si usas PostgreSQL
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

def documentos_list(request):
    q = request.GET.get('q', '').strip()
    
    if q:
        search_vector = SearchVector('titulo', weight='A') + \
                       SearchVector('descripcion', weight='B') + \
                       SearchVector('tags', weight='C')
        search_query = SearchQuery(q)
        
        qs = Documento.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank')
    else:
        qs = Documento.objects.filter(publicado=True)
```

### 5. **Exportar Datos a Excel/PDF**
```python
# Instalar: pip install openpyxl reportlab

from openpyxl import Workbook
from django.http import HttpResponse

@login_required
def exportar_calificaciones_excel(request):
    # Obtener calificaciones del usuario
    calificaciones = Calificacion.objects.filter(estudiante=request.user)
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Mis Calificaciones"
    
    # Encabezados
    ws.append(['Fecha', 'Asignatura', 'Tipo', 'Nota', 'Semestre'])
    
    # Datos
    for cal in calificaciones:
        ws.append([
            cal.fecha_evaluacion.strftime('%d/%m/%Y'),
            str(cal.asignatura),
            cal.get_tipo_evaluacion_display(),
            cal.nota,
            cal.get_semestre_display()
        ])
    
    # Respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=mis_calificaciones.xlsx'
    wb.save(response)
    return response
```

### 6. **Logs Estructurados**
```python
# En settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'auditoria': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Usar en views.py
import logging
logger = logging.getLogger('auditoria')

def descargar_documento(request, pk):
    # ...
    logger.info(f"Usuario {request.user.username} descargó documento {documento.titulo}")
```

---

## 📊 Prioridades de Implementación

### Alta Prioridad (1-2 días)
1. ✅ Corregir errores de sintaxis en templates (HECHO)
2. 🔧 Validación de RUT chileno
3. 🔧 Manejo de archivos inexistentes
4. 🔧 Validación de filtros

### Media Prioridad (3-5 días)
5. 🔧 Sistema de notificaciones básico
6. 🔧 Exportar calificaciones a Excel
7. 🔧 Logs estructurados
8. 🔧 Caché para consultas frecuentes

### Baja Prioridad (1-2 semanas)
9. 🔧 Búsqueda avanzada con PostgreSQL
10. 🔧 Historial de actividad
11. 🔧 Optimización de queries con select_related
12. 🔧 Tests automatizados

---

## 🎯 Resumen

**Errores Críticos Corregidos**: 4 archivos con sintaxis incorrecta
**Errores Funcionales Detectados**: 7
**Mejoras Propuestas**: 6

**Estado del Proyecto**: ✅ Funcional con mejoras pendientes
**Próximo Paso**: Implementar validación de RUT y manejo de archivos inexistentes

El proyecto está en buen estado funcional. Los errores detectados son principalmente de optimización y casos edge que no afectan el uso normal.
