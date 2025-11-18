# Catálogo de Errores Django - Plataforma Educativa Liceo Juan Bautista de Hualqui

## 🚨 Checklist Rápido de "Salida de Emergencia"

1. `DEBUG=False`, `ALLOWED_HOSTS` correcto y `SECRET_KEY` por entorno.
2. `INSTALLED_APPS`, `MIDDLEWARE` y `TEMPLATES` con *context processors* necesarios.
3. Migraciones limpias: `makemigrations && migrate`, sin conflictos.
4. Autenticación y permisos probados desde sesión incógnita (panel privado inaccesible sin login).
5. Estáticos/medios visibles en prod (`collectstatic`, Whitenoise o servidor).
6. Formularios con CSRF, validaciones y mensajes visibles.
7. Consultas optimizadas en listados (usa `select_related/prefetch_related`).
8. Logs activados y *ERROR pages* personalizadas operativas.
9. Datos personales minimizados en vistas públicas; cumplimiento legal.
10. Mini-suite de pruebas: login correcto/incorrecto, acceso restringido, crear/listar noticias, paginación, formulario de contacto (render), y un test de permisos del admin.

---

## 🔧 Errores Comunes Específicos para Nuestro Proyecto

### 🔐 Autenticación con RUT
- **Problema**: Login falla por formato de RUT inconsistente
- **Solución**: Normalizar RUT en el modelo y validación completa
- **Archivo**: `usuarios/models.py` - función `validar_rut_completo()`

### 📰 Sistema de Noticias
- **Problema**: Búsqueda de noticias no encuentra resultados
- **Solución**: Verificar filtros en `noticias_list.html` y `comunicacion/views.py`
- **Archivo**: `comunicacion/templates/comunicacion/noticias_list.html`

### 👨‍🏫 Panel del Profesor
- **Problema**: Vista de profesor no encuentra estudiantes
- **Solución**: Verificar relaciones ForeignKey y permisos
- **Archivo**: `academico/profesor_views.py` - función `panel_profesor()`

### 📊 Calificaciones
- **Problema**: Cálculo de promedios falla
- **Solución**: Validar rangos 1.0-7.0 y manejo de `None`
- **Archivo**: `academico/templates/academico/profesor_gestionar_calificaciones.html`

### 📧 Envío de Correos
- **Problema**: Función de correos no envía (por ahora solo visual)
- **Solución**: Verificar formulario y validación en JavaScript
- **Archivo**: `academico/templates/academico/profesor_enviar_correos.html`

---

## 📋 Lista Completa de Errores por Área

### # Errores de configuración y entorno

**Variables de entorno mal cargadas (SECRET_KEY, DEBUG, DB, EMAIL).** Sucede cuando `settings.py` lee valores inexistentes o con tipos incorrectos. Verás `ImproperlyConfigured` o credenciales fallidas al iniciar el servidor. Revisa `.env`, tipos (bool/str/int) y que el `.env` se cargue antes de usarlo. Solución rápida: valores por defecto seguros y `print(os.environ.get("..."))` en local.

**`ALLOWED_HOSTS` vacío en producción.** En local funciona con `DEBUG=True`, pero en producción devuelve *Bad Request (400)*. Añade tu dominio/IP a `ALLOWED_HOSTS`. Si usas proxy, agrega el host interno.

**Reloj/zonas horarias mal configuradas.** Fechas "saltadas", expiración de sesión rara, o timestamps incoherentes. Revisa `TIME_ZONE="America/Santiago"` y `USE_TZ=True`. Conviertes a *aware*/*naive* consistentemente.

**Orden de `MIDDLEWARE` incorrecto.** Errores de CSRF, sesiones que no persisten o redirects raros. `SecurityMiddleware` primero, `AuthenticationMiddleware` antes de código que usa `request.user`, `MessageMiddleware` antes de mostrar mensajes, `CommonMiddleware` y `XFrameOptionsMiddleware` en orden recomendado.

**Apps no registradas o con nombre errado.** `AppRegistryNotReady` o `LookupError: No installed app named...`. Asegura que cada app esté en `INSTALLED_APPS` con su *config* correcta (`app.apps.AppConfig`).

### # Base de datos y migraciones

**Migraciones fuera de sincronía.** Cambiaste modelos sin generar/aplicar migraciones → `OperationalError`, `InconsistentMigrationHistory` o campos inexistentes. Ejecuta `makemigrations` + `migrate`, evita editar migraciones ya aplicadas. Si te atascas, usa `--fake` con criterio y respalda.

**Conflictos de migraciones entre ramas.** `Conflicting migrations detected`. Causa: dos migraciones paralelas que tocan lo mismo. Solución: `makemigrations --merge` y resuelve a mano el archivo de *merge*.

**Integridad referencial rota.** `IntegrityError` por `ForeignKey` sin objeto padre, duplicados en `unique`. Agrega validaciones en formularios y señales, usa `on_delete` correcto, y manéjalo con transacciones.

**Lock de SQLite o rendimiento pobre.** En desarrollo, "database is locked" con múltiples hilos. Cierra conexiones, evita operaciones pesadas en requests y considera Postgres para paralelo real.

### # Ruteo, URLs y navegación

**`NoReverseMatch`.** Nombre de URL mal escrito o sin argumentos requeridos. Usa `reverse('nombre', kwargs={'id':obj.id})` y verifica nombres en `urls.py`. Mantén consistencia al renombrar rutas.

**Conflictos de prefijos o includes repetidos.** Dos `path()` capturan lo mismo y el esperado nunca se ejecuta. Ordena de específico a genérico. Evita *catch-alls* antes de rutas concretas.

**Vista 404 personalizada no encontrada.** `404.html` fuera de templates o bloque heredado mal definido. Asegura que esté en la raíz de templates y sin errores de sintaxis.

### # Plantillas y contexto

**`TemplateDoesNotExist`.** Ruta de template incorrecta o `DIRS` en `TEMPLATES` mal configurado. Verifica `APP_DIRS=True` o rutas absolutas correctas. Usa `django.template.loaders` en *DEBUG* para ver búsquedas.

**Faltan variables en contexto.** Aparecen bloques vacíos o errores de filtro. Agrega *context processors* a `TEMPLATES['OPTIONS']['context_processors']`. Maneja `None` en templates con `default`/condicionales.

**Filtros o tags de terceros no cargados.** Con `crispy-forms`, falta `{% load crispy_forms_tags %}` → etiquetas no reconocidas. Carga el tag y verifica versión de `crispy-bootstrap5`.

### # Formularios, validación y CSRF

**Fallo de token CSRF.** Observado como *403 CSRF verification failed*. Causas: método POST sin `{% csrf_token %}`, dominios cruzados, cookies bloqueadas. Incluye el token, revisa `CSRF_TRUSTED_ORIGINS` en prod y SameSite de cookies.

**Validaciones débiles o no mostradas.** El formulario "envía" pero no valida, o los errores no se ven. Asegura `form.is_valid()`, renderiza `{{ form.non_field_errors }}` y `{{ form.field.errors }}`. Con `crispy`, define `helper` y *layout* correctamente.

**Normalización del RUT.** Logins fallan por formatos distintos (`12.345.678-9` vs `12345678-9`). Crea un *validator* que limpie puntos/guion, verifique dígito verificador, y guarda un formato canónico. Evita *case-sensitive*.

### # Autenticación, autorización y sesiones

**Restricción de acceso mal aplicada.** Vistas privadas accesibles sin login o, al revés, usuarios legítimos ven 403. Usa `@login_required`, `LoginRequiredMixin`, y permisos (`user.is_staff`) en panel admin link. Prueba rutas protegidas desde incógnito.

**Redirecciones de login/next rotas.** Tras autenticarse vuelve al login o se pierde `?next=`. Configura `LOGIN_URL`, `LOGIN_REDIRECT_URL` y respeta `next` en la vista.

**Sesiones que expiran antes de tiempo.** Ajusta `SESSION_COOKIE_AGE`, `SESSION_EXPIRE_AT_BROWSER_CLOSE`. Verifica caché si usas *cache-backed sessions*.

### # Modelo, consultas y rendimiento

**Consultas N+1.** Listados de noticias con `obj.autor` o `obj.categorias` provocan múltiples queries. Usa `select_related`/`prefetch_related`. Mide con *Django Debug Toolbar* en desarrollo.

**Filtros y ordenamientos inseguros.** Tomar parámetros GET y pasarlos directo a `order_by()` o `filter()` puede romper o exponer datos. Valida listas blancas de campos. Maneja `ValueError`.

**`DoesNotExist` y `MultipleObjectsReturned`.** Captura ambos al buscar por campos no únicos. Para detalle de noticia, usa `get_object_or_404`.

**Paginación rota.** `?page=` inválida lanza `EmptyPage`. Maneja con `Paginator` y `page_obj` seguro, redirige a última página válida.

### # Admin de Django

**`list_display` con campos inexistentes.** Fallará al cargar el admin. Revisa nombres exactos o métodos con `short_description`. Lo mismo para `search_fields`, `list_filter`, `ordering`.

**Acciones admin que no validan permisos.** Personalizas `save_model`/`get_queryset` sin respetar `request.user` → exposición de datos. Filtra por permisos y roles.

**Campos `readonly_fields` que dependen de cálculos frágiles.** Si acceden a relaciones nulas, revientan. Protege con `if obj and obj.rel`.

### # Archivos estáticos y medios

**`collectstatic` falla o no sirve en prod.** `STATIC_ROOT` sin permisos, o no configuraste servidor web/Whitenoise. Define `STATIC_URL/STATIC_ROOT`, corre `collectstatic`, y en producción sirve estáticos desde Nginx/Whitenoise.

**Rutas de `MEDIA_*` mal configuradas.** Cargas de archivos fallan o no se muestran. Define `MEDIA_URL` y `MEDIA_ROOT`, crea vista/servidor para servirlos en dev, en prod usa almacenamiento en disco o S3.

**Permisos de archivo.** Errores de lectura/escritura en contenedores o hosting compartido. Ajusta permisos y usuario del proceso (uWSGI/Gunicorn).

### # Seguridad y cumplimiento

**CSRF/XSS/Clickjacking.** Falta de `SecurityMiddleware`, `X_FRAME_OPTIONS`, o escapado de variables. Mantén autoescapado, usa `{{ variable|safe }}` solo si confías, y `SECURE_*` en HTTPS (HSTS, cookies seguras).

**Exposición de datos personales.** Mostrar RUT, correos o logs sensibles en páginas públicas o *DEBUG*. Usa `DEBUG=False` en prod, loguea de forma anónima y oculta datos en templates.

**CORS y orígenes no confiables.** Abrir CORS a `*` permite abuso. Si expones API, limita orígenes y métodos.

**Claves en el repo.** Subir `SECRET_KEY`/`.env` por error. Usa `.gitignore`, rota credenciales si ocurrió alguna vez.

### # Mensajería y UX

**Mensajes que no aparecen.** `messages` configurado pero faltan bloques en templates. Añade el loop de mensajes en `base.html` y categorías Bootstrap.

**Estados sin feedback.** Formulario de contacto "visual" sin enviar datos puede confundir. Muestra *flash* claro de "solo visual/demostrativo".

### # Internacionalización y formato

**i18n/l10n inconsistentes.** Fechas y números con formato incorrecto. Activa `USE_I18N`/`USE_L10N`, usa filtros `localize` y plantillas de `formats` si necesitas DD/MM/YYYY.

**Normalización de mayúsculas/acentos en búsquedas.** Búsquedas que no encuentran por tildes. Considera `icontains`, extensiones de Postgres (unaccent) o preprocesa términos.

### # Concurrencia y transacciones

**Condiciones de carrera al inscribir a talleres.** Dos usuarios crean cupo a la vez superando el límite. Usa transacciones `select_for_update()` y valida cupos dentro de una vista atómica.

**Actualizaciones parciales.** Guardar modelos en múltiples pasos sin `atomic()` puede dejar datos a medias si hay excepción. Encapsula operaciones críticas.

### # Capa de servicios externos

**Email backend inválido.** Si en el futuro activas envío real, fallará por credenciales/puertos. Prueba con `console.EmailBackend` en dev; en prod usa TLS/PUERTO correcto y timeouts.

**CAPTCHA/anti-spam mal integrados.** Rupturas de flujo si el widget no carga o la secret key no coincide. Maneja *graceful degradation*.

### # Despliegue y servidor

**Gunicorn/uWSGI mal configurado.** Timeouts, workers insuficientes o *memory leaks*. Ajusta número de workers según CPU, usa *health checks* y *graceful reloads*.

**Proxy/HTTPS mal terminado.** `SECURE_PROXY_SSL_HEADER` sin setear con Nginx/Cloudflare produce URLs *http* y cookies inseguras. Configura el encabezado correcto (`HTTP_X_FORWARDED_PROTO`).

**Estáticos servidos por Django en prod.** Consumen CPU y bloquean workers. Sirve estáticos desde CDN/Nginx/Whitenoise.

### # Pruebas y calidad

**Tests frágiles dependientes de hora/locale.** Cambian con la fecha. *Freeze time* o usa zonas horarias fijas en tests. Evita asserts de cadenas completas con tildes/espacios.

**Fixtures desalineadas con migraciones.** Tests que cargan fixtures antiguas revienta `migrate`. Regenera fixtures tras cambios de modelo.

**Cobertura baja en flujos críticos.** Autenticación por RUT, inscripción a talleres, y permisos del panel deben tener al menos un test que falle si algo cambia.

### # Rendimiento en producción

**Caché mal usada.** Claves sin *versionado* o *invalidación* provocan datos viejos. Prefiere *per-view cache* en listados, y define una estrategia de invalidación.

**Assets pesados.** Imágenes de noticias sin optimizar ralentizan. Comprime, redimensiona y usa `srcset`/lazy-loading.

### # Logging y observabilidad

**Sin logs útiles en prod.** Cuando algo falla, no hay rastro. Configura `LOGGING` con formateadores, niveles por módulo y handlers a archivo/STDOUT. Añade IDs de petición si usas proxy.

**Excepciones "tragadas".** `try/except` amplios que silencian errores. Loguea con `logger.exception()` y devuelve mensajes de usuario seguros.

### # Documentación y mantenimiento

**README/entorno incompletos.** En un PC nuevo no se puede levantar. Incluye pasos: crear venv, `pip install -r requirements.txt`, `migrate`, `createsuperuser`, `runserver`, y variables requeridas.

**Requisitos desalineados (`requirements.txt`).** Falta `crispy-bootstrap5` o versión incompatible. Congela versiones conocidas buenas (`pip freeze`) y actualiza con cautela.

---

## 🎯 Errores Específicos de Nuestra Implementación

### Autenticación con RUT Chileno
- **Problema**: Algoritmo de validación de RUT incorrecto
- **Solución**: Usar el algoritmo oficial chileno
- **Archivo**: `usuarios/models.py` - `validar_rut_completo()`

### Panel del Profesor - Gestión de Calificaciones
- **Problema**: Cálculo de promedios falla con valores nulos
- **Solución**: Validar antes de calcular, usar `if nota and nota > 0`
- **Archivo**: `academico/profesor_views.py` - `gestionar_calificaciones()`

### Sistema de Noticias - Búsqueda
- **Problema**: Filtros no funcionan correctamente
- **Solución**: Validar parámetros GET antes de usar
- **Archivo**: `comunicacion/views.py` - `noticias_list()`

### Envío de Correos - Solo Visual
- **Problema**: Usuarios esperan envío real
- **Solución**: Mostrar claramente que es solo demostración
- **Archivo**: `academico/templates/academico/profesor_enviar_correos.html`

### Base de Datos Académica
- **Problema**: Relaciones ForeignKey pueden fallar
- **Solución**: Usar `get_object_or_404` y manejo de errores
- **Archivo**: `academico/profesor_views.py` - `mis_estudiantes()`

---

## 📊 Comandos de Diagnóstico

```bash
# Verificar estado de migraciones
python manage.py showmigrations

# Probar conexión a base de datos
python manage.py dbshell

# Limpiar archivos estáticos
python manage.py collectstatic --noinput

# Verificar configuración
python manage.py check

# Crear superusuario
python manage.py createsuperuser

# Ejecutar con debug verbose
python manage.py runserver --verbosity=2
```

---

## 🚨 Errores Críticos para Evitar

1. **RUT mal validado** → Login falla
2. **Permisos mal configurados** → Acceso no autorizado
3. **Migraciones desincronizadas** → Errores de base de datos
4. **Formularios sin CSRF** → Vulnerabilidad de seguridad
5. **Archivos estáticos no servidos** → Páginas sin estilo
6. **DEBUG=True en producción** → Exposición de datos sensibles
7. **SECRET_KEY en repo** → Vulnerabilidad crítica
8. **Consultas N+1** → Performance pobre
9. **Sin manejo de errores** → Páginas rotas
10. **Sin backups** → Pérdida de datos

---

## ✅ Lista de Verificación Pre-Despliegue

- [ ] Migraciones aplicadas sin errores
- [ ] DEBUG=False en producción
- [ ] ALLOWED_HOSTS configurado
- [ ] SECRET_KEY segura
- [ ] Archivos estáticos servidos correctamente
- [ ] Formularios con CSRF
- [ ] Autenticación con RUT funcionando
- [ ] Panel del profesor accesible solo a profesores
- [ ] Sistema de noticias con búsqueda operativa
- [ ] Base de datos con datos de prueba
- [ ] Logs configurados
- [ ] Permisos de archivo correctos
- [ ] SSL/HTTPS configurado
- [ ] Backups programados
- [ ] Documentación actualizada

¡Con esta lista tendrás una plataforma robusta y libre de errores comunes! 🎉
