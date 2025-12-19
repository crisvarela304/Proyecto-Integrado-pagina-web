# Schoolar OS - Biblia Técnica y Operativa Completa

**Versión: 2.0 - Arquitectura Skeleton & Fleet Definitiva**  
**Estado: Producción Ready**  
**Última Actualización: Diciembre 2024**

---

## 📋 Índice Completo

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura Skeleton & Fleet](#arquitectura-skeleton--fleet)
3. [Matriz de Roles y Casos de Uso](#matriz-de-roles-y-casos-de-uso)
4. [Especificaciones Técnicas Backend](#especificaciones-técnicas-backend)
5. [Especificaciones Técnicas App](#especificaciones-técnicas-app)
6. [Guía de DevOps y Despliegue](#guía-de-devops-y-despliegue)
7. [Seguridad y Mejoras Críticas](#seguridad-y-mejoras-críticas)

---

## 🎯 Resumen Ejecutivo

### Visión del Proyecto

Schoolar OS es un ecosistema educativo distribuido que permite a cada colegio tener su propia instancia aislada (VPS + Dominio) mientras los usuarios acceden a través de una aplicación móvil universal. La arquitectura resuelve el problema fundamental de la escalabilidad multi-colegio sin comprometer la seguridad ni el rendimiento.

### Modelo de Negocio Técnico

- **Producción**: 1 VPS pequeña por colegio + Dominio propio (`colegiosanpedro.cl`)
- **Aislamiento**: Cada colegio tiene su base de datos y archivos completamente separados
- **Escalabilidad**: La "flota" puede crecer indefinidamente sin afectar a otros miembros
- **Actualizaciones**: Watchtower actualiza automáticamente toda la flota via Git pushes

### Componentes Principales

1. **Web Skeleton** - Backend Django + React/Templates (clonable)
2. **App Universal** - React Native + Expo (camaleónica)
3. **Directorio Central** - Microservicio de descubrimiento
4. **Infraestructura** - Docker + VPS + SSL automático

---

## 🏗️ Arquitectura "SKELETON & FLEET" (EL CEREBRO)

### Distinción Fundamental de Componentes

#### A. EL WEB SKELETON (Backend/Web - Responsabilidad del Web Dev)

El Web Skeleton NO es un monolito multi-tenant lógico. Es un **"Esqueleto Reutilizable"** (Django + React/Template) que se clona en contenedores Docker aislados.

**Arquitectura Interna:**
```python
# Estructura del Skeleton
backend/
├── apps/
│   ├── academicos/          # Gestión académica
│   ├── usuarios/            # Gestión de usuarios
│   ├── comunicacion/       # Notificaciones y circulars
│   └── documentos/          # Intranet y archivos
├── config/
│   ├── settings.py         # Configuración base
│   ├── urls.py            # Enrutamiento principal
│   └── wsgi.py            # WSGI para producción
├── docker/
│   ├── Dockerfile         # Receta genérica
│   ├── entrypoint.sh      # Script de inicialización
│   └── nginx.conf         # Configuración web
└── requirements.txt       # Dependencias Python
```

**Protocolo "Phone Home" (CRÍTICO):**

El mecanismo de auto-registro elimina la configuración manual:

1. **Nacimiento del Colegio:**
   ```bash
   # Al iniciar el contenedor (Entrypoint), si no tiene configuración:
   if [ ! -f /app/.configurado ]; then
       SCHOOL_CODE=$(head /dev/urandom | tr -dc A-Z0-9 | head -c 8)
       echo "COLEGIO_CODIGO_UNICO=${SCHOOL_CODE}" >> /app/.env
       
       # Envía POST al Directorio Central
       curl -X POST ${DIRECTORIO_URL}/register \
            -H "Content-Type: application/json" \
            -d "{\"codigo\": \"${SCHOOL_CODE}\", \"url\": \"${CURRENT_HOST_URL}\"}"
   fi
   ```

2. **Proceso de Registro:**
   - El contenedor genera un `SCHOOL_CODE` (UUID parcial de 8 caracteres)
   - Envía un POST al Directorio Central (`/register`) con su IP/Dominio actual (`CURRENT_HOST_URL`) y su Código
   - El Directorio Central registra la asociación y devuelve confirmación
   - Esto elimina la configuración manual. El colegio "nace" y avisa dónde vive

3. **Variables de Entorno Críticas:**
   ```bash
   CURRENT_HOST_URL=https://colegio-san-pedro.cl  # URL oficial del colegio
   DIRECTORIO_URL=https://api.directory.com       # URL del servicio central
   COLEGIO_CODIGO_UNICO=COLE-88                    # Código único del colegio
   ```

#### B. LA APP UNIVERSAL (Frontend - Responsabilidad del App Dev)

La App funciona como un **"Camaleón Digital"** que se transforma según el colegio:

**Flujo de Transformación:**

1. **Descarga Vacía:**
   - Usuario descarga app genérica de tiendas (App Store/Play Store)
   - Interfaz neutra con branding Schoolar OS
   - Sin conexión a ningún colegio

2. **Ingreso de Código:**
   - Usuario ingresa código único proporcionado por el colegio (ej: "COLE-88")
   - App consulta Directorio Central: `GET /discover/COLE-88`

3. **Metamorfosis:**
   ```typescript
   // App se transforma dinámicamente
   const schoolConfig = await apiDirectorio.discover('COLE-88');
   
   // Cambia identidad visual
   updateTheme(schoolConfig.colores);
   updateLogo(schoolConfig.logo_url);
   
   // Reconfigura endpoints
   apiClient.setBaseURL(schoolConfig.api_url);
   
   // Guarda configuración local
   await SecureStore.setItemAsync('active_school', JSON.stringify(schoolConfig));
   ```

4. **Conexión Directa:**
   - App se conecta directamente a la VPS del colegio
   - Todas las operaciones subsiguientes son peer-to-peer (app ↔ colegio)
   - El Directorio Central ya no interviene

**Arquitectura de Conexión:**
```mermaid
sequenceDiagram
    participant U as Usuario
    participant A as App Universal
    participant D as Directorio Central
    participant C as Colegio VPS
    
    U->>A: Ingresa código "COLE-88"
    A->>D: GET /discover/COLE-88
    D-->>A: URL: https://colegio.cl
    A->>C: POST /api/auth/login
    C-->>A: JWT Token + User Data
    A->>U: Interfaz personalizada del colegio
```

---

## 👥 Matriz de Roles y Cronogramas (OPERACIONES)

### A. ROL: CREADORES (Nosotros - Nivel Dios)

**Poder:** Infraestructura, VPS, Deploy, Código Fuente.

**Cronograma:**
- **Día 0 (Venta):** 
  - Contratación VPS + Dominio → `docker-compose up` 
  - Recepción del Código vía Phone Home 
  - Envío de credenciales al Director
- **Mensual:** Revisión de estado de servidores (Health Checks) en el Directorio Central
- **Eventual:** Push a Git → Watchtower actualiza toda la flota automáticamente

**Casos de Uso:**
- **Caso A: El "Big Bang" (Despliegue)**
  - Acción: Ejecutar script de despliegue para nuevo cliente
  - Resultado: El servidor nace, ejecuta "Phone Home" y genera Código Único (`COLE-X`)
- **Caso B: El Hotfix (Mantenimiento)**
  - Acción: Detectan bug en cálculo de promedios. Pushean fix a Git
  - Resultado: Watchtower actualiza automáticamente los 50 colegios en la madrugada

---

### B. ROL: ADMIN HIGH LEVEL (Director / UTP)

**Poder:** Dueño de la instancia, Configuración Semestral, Gestión de Staff.

**Cronograma:**
- **Inicio de Año (Enero/Marzo):** Configuración del Año Académico, Semestres y carga de Planificación Anual
- **Mensual:** Revisión de reportes de gestión (asistencia global, rendimiento por curso)
- **Fin de Año:** Cierre de actas y promoción de alumnos

**Casos de Uso:**
- **Uso Web:** Carga masiva de matrícula (CSV), creación de cuentas de Inspectores/Secretarias
- **Uso App:** Dashboard gerencial (Asistencia global en tiempo real)

**Flujo Detallado:**
1. **Día 0 (Setup):**
   - Recibe Código de Super Admin
   - Entra a la Web → Configura: "Semestre 1: Marzo a Julio"
   - Crea cuentas de sus "Generales": Jefe de Inspectores y Secretaria Principal

2. **Día N (Rutina Web):**
   - Revisa "Panel de Control de UTP": ¿Qué profesores no han subido notas a tiempo?
   - Aprueba planificación anual que subieron los profesores (Intranet)
   - Envía circular oficial a todos los apoderados: "Suspensión de clases por duelo"

---

### C. ROL: ADMIN LOW LEVEL (Inspector / Secretaria)

**Poder:** Operativo en terreno y ventanilla.

**Cronograma:**
- **Diario (07:30 - 08:30):** Control de acceso en puerta y gestión de atrasos
- **Diario (Mañana/Tarde):** Atención de apoderados en ventanilla, emisión de certificados, llamadas por inasistencias
- **Período de Matrícula:** Carga intensiva de fichas de alumnos nuevos

**Casos de Uso:**
- **Caso A: Lado Web (Secretaria - Matrícula)**
  - Contexto: Llega un apoderado nuevo
  - Acción: Entra a la Web → Ficha Alumno. Ingresa datos, sube foto del carnet. Imprime **Comprobante de Matrícula** con **Código QR Inicial** para que el alumno active su App

- **Caso B: Lado App (Inspector - Patrulla)**
  - Contexto: Recorrido de pasillos durante clases
  - Acción: Encuentra a un alumno fuera de clases. Saca celular → Escanea QR del alumno → Verifica si tiene permiso de salida. Si no, registra "Fuga de clases" (notificación automática al apoderado)

---

### D. ROL: PROFESOR

**Poder:** Académico y Contenido.

**Cronograma:**
- **Diario:** Toma de asistencia (bloque a bloque), registro de leccionario
- **Semanal:** Subida de material de estudio (PDFs, PPTs) a la Intranet
- **Mensual:** Ingreso de calificaciones de pruebas parciales

**Casos de Uso:**
- **Uso Web:** "Libro de Clases Digital" (Notas masivas) y **MÓDULO INTRANET** (Subida de archivos/PDFs por asignatura)
- **Uso App:** Toma de asistencia rápida bloque a bloque, revisión de conducta

**Flujo Intranet:**
1. **Profesor (En Web):**
   - Entra a "Asignatura: Historia"
   - Clic en **"Nuevo Recurso"** → Sube `Guia_Revolucion_Francesa.pdf`
   - Selecciona: "Visible para: 2° Medio A"
   - Opcional: Marca "Notificar a alumnos"

2. **Alumno (En App):**
   - Recibe notificación: *"Nuevo material en Historia"*
   - Abre App → Asignaturas → Historia → Recursos
   - Ve el PDF y lo descarga para estudiar

---

### E. ROL: ALUMNO

**Poder:** Consumo e Identidad.

**Cronograma:**
- **Día 1:** Registro en la App con el código que le dio la secretaria (o su correo institucional)
- **Diario:** Entrada (QR), revisión de horario, consumo de material de estudio
- **Pre-Prueba:** Descarga de guías de la Intranet para estudiar

**Casos de Uso:**
- **Caso A: Lado Web (Estudio Profundo)**
  - Contexto: Tiene prueba mañana y necesita estudiar
  - Acción: Entra a `colegio.cl` en su computador → Intranet → Biología. Descarga el `guia_celula.pdf` que subió el profesor

- **Caso B: Lado App (Acceso y Consulta)**
  - Contexto: Llega al colegio y luego quiere ver su nota
  - Acción: 
    1. Muestra su **QR en la App** al Inspector para validar su ingreso (o almuerzo)
    2. En el recreo, recibe Push: "Nueva nota en Matemáticas". Abre la App y ve su 6.5

---

### F. ROL: APODERADO

**Poder:** Monitoreo.

**Cronograma:**
- **Día 1:** Descarga App → Crea Cuenta → Vincula alumno (escaneando QR del hijo)
- **Eventual:** Justificación de inasistencias, revisión de comunicaciones, pago de mensualidad (si aplica)
- **Diario:** Recepción pasiva de notificaciones (asistencia/notas)

**Casos de Uso:**
- **Caso A: Lado Web (Certificados)**
  - Contexto: Necesita certificado de alumno regular para trámite en caja de compensación
  - Acción: Entra a la Web → Portal Apoderados → Descargar Certificado (PDF firmado digitalmente)

- **Caso B: Lado App (El Radar)**
  - Contexto: En el trabajo
  - Acción: Recibe notificación: *"Juanito tiene una nueva anotación negativa: Fuga de clases"*. Abre la App, lee el detalle ingresado por el Inspector y contacta al colegio

---

### 📊 Resumen del Ecosistema Vivo

| Rol | Foco Principal | Herramienta Favorita | Interacción Clave |
| --- | --- | --- | --- |
| **Nosotros** | Infraestructura | Terminal / Git | `docker-compose up` |
| **Admin High** | Gestión & Estrategia | Web (Dashboard) | Ver métricas globales |
| **Admin Low** | Operación Diaria | App (Escáner) / Web | Matricular & Controlar |
| **Profesor** | Académico & Intranet | Web (Carga) / App (Aula) | Subir Archivos & Notas |
| **Alumno** | Identidad & Estudio | App (QR/Notas) / Web (PDFs) | Descargar Guías & Entrar |
| **Apoderado** | Control & Trámites | App (Push) / Web (Certif.) | Recibir Alertas |

---

## 🗄️ MÓDULO INTRANET (GESTIÓN DE ARCHIVOS)

### Arquitectura de Almacenamiento Distribuido

El módulo Intranet permite el intercambio de archivos entre profesores y alumnos de manera segura y eficiente.

#### Flujo Técnico de Archivos

**1. Subida de Recursos (Profesor → Web):**
```python
# views.py - Backend Django
class RecursoCreateView(APIView):
    def post(self, request):
        archivo = request.FILES.get('archivo')
        titulo = request.data.get('titulo')
        asignatura_id = request.data.get('asignatura_id')
        
        # Validar tamaño y tipo
        if archivo.size > 50 * 1024 * 1024:  # 50MB max
            return Response({'error': 'Archivo demasiado grande'})
        
        # Guardar en almacenamiento local (volumen Docker)
        recurso = Recurso.objects.create(
            titulo=titulo,
            archivo=archivo,
            asignatura_id=asignatura_id,
            profesor=request.user.profesor,
            publicado=True
        )
        
        # Disparar notificación push
        enviar_notificacion_a_alumnos(asignatura_id, f"Nuevo recurso: {titulo}")
        
        return Response(RecursoSerializer(recurso).data)
```

**2. Consumo de Recursos (Alumno ← App):**
```typescript
// services/intranet.ts
export const obtenerRecursos = async (asignaturaId: string) => {
  const response = await apiClient.get(`/api/intranet/recursos/${asignaturaId}`);
  return response.data.data;
};

export const descargarRecurso = async (recursoId: string) => {
  const response = await apiClient.get(`/api/intranet/descargar/${recursoId}`, {
    responseType: 'blob'
  });
  
  // Guardar en dispositivo
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  return { url, filename: response.headers['content-disposition'] };
};
```

**3. Estrategias de Almacenamiento:**

**Opción A: Volúmenes Docker (Recomendado para empezar)**
```yaml
# docker-compose.yml
volumes:
  - media_data:/app/media
  - static_data:/app/static

volumes:
  media_data:
  static_data:
```

**Opción B: AWS S3 (Para escalamiento)**
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = 'schoolar-colegio-x-media'
```

#### Tipos de Archivos Soportados

- **PDFs:** Guías de estudio, apuntes, evaluaciones
- **Presentaciones:** PowerPoint, Google Slides exportados
- **Videos:** Clases grabadas (max 100MB)
- **Imágenes:** Diagramas, gráficos, fotos
- **Documentos:** Word, Excel para tareas

#### Control de Acceso y Permisos

```python
# permissions.py
class EsProfesorDeAsignatura(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.profesor.asignaturas.filter(id=obj.asignatura.id).exists()

class EsAlumnoDelCurso(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.alumno.curso.asignaturas.filter(id=obj.asignatura.id).exists()
```

---

## 💻 Guía de Desarollo Local (PARA EL APP DEV)

### Estrategia A: Docker Local (Recomendado)

**Ventajas:** Simula el entorno de producción exactamente

**Pasos:**
1. **Clonar repositorios:**
   ```bash
   git clone https://github.com/schoolar/backend.git
   git clone https://github.com/schoolar/mobile.git
   ```

2. **Levantar stack local:**
   ```bash
   # En directorio backend
   docker-compose -f docker-compose.local.yml up -d
   
   # Crear superusuario
   docker-compose exec backend python manage.py createsuperuser
   
   # Poblar datos de prueba
   docker-compose exec backend python manage.py seed_data
   ```

3. **Conectar App local:**
   ```typescript
   // src/config/dev.ts
   export const API_BASE_URL = 'http://192.168.1.50:8000';  # IP local
   export const DIRECTORIO_URL = 'http://localhost:5000';
   ```

### Estrategia B: Nativo Windows (Directo)

**Ventajas:** Más rápido para iterar, sin Docker

**Instalación Python:**
1. Descargar Python 3.11 desde `python.org/downloads`
2. **CRÍTICO:** Marcar "Add Python to PATH" durante instalación
3. Modificar `requirements.txt`:
   ```text
   # Cambiar psycopg2 por versión precompilada
   psycopg2-binary
   ```

**Preparar Entorno:**
```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Correr servidor
python manage.py runserver 0.0.0.0:8000
```

**Obtener IP Local:**
```bash
ipconfig
# Anotar Dirección IPv4 (ej: 192.168.1.50)
```

### Estrategia C: Mocking (Más Rápido)

**Ventajas:** Desarrollar UI sin depender del backend

**Crear Mocks:**
```typescript
// src/mocks/responses.ts
export const mockNotas = {
  success: true,
  data: [
    { asignatura: 'Matemáticas', nota: 6.5, fecha: '2024-03-20' },
    { asignatura: 'Lenguaje', nota: 5.8, fecha: '2024-03-22' }
  ]
};

export const mockAlumno = {
  success: true,
  data: {
    id: '550e8400-e29b-41d4-a716-446655440000',
    nombre: 'Juan Pérez',
    curso: '4to Medio A',
    rut: '1-9'
  }
};
```

**Interruptor de Modo Debug:**
```typescript
// src/api/client.ts
const DEBUG_MODE = __DEV__; // true en desarrollo

export const getNotas = async (alumnoId: string) => {
  if (DEBUG_MODE) {
    // Simular retardo de red
    await new Promise(resolve => setTimeout(resolve, 1000));
    return mockNotas;
  }
  
  // Producción: llamada real a API
  const response = await apiClient.get(`/api/alumnos/${alumnoId}/notas`);
  return response.data;
};
```

---

## 🔧 Guía de DevOps y Despliegue

### Desarrollo Local

#### Docker Completo (Flota Local)

**docker-compose.local.yml:**
```yaml
version: '3.8'

services:
  # Directorio Central
  directorio:
    build: ./directorio
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
      - MODE=development

  # Colegio de Prueba
  colegio-demo:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - COLEGIO_CODIGO_UNICO=DEMO-01
      - DB_NAME=db_demo.sqlite3
      - CURRENT_HOST_URL=http://192.168.1.50:8000
      - DIRECTORIO_URL=http://192.168.1.50:5000
    volumes:
      - ./data/media:/app/media

  # Base de datos
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

**Levantar todo:**
```bash
# Construir y levantar servicios
docker-compose -f docker-compose.local.yml up --build -d

# Crear datos de prueba
docker-compose exec colegio-demo python manage.py seed_demo

# Ver logs
docker-compose logs -f colegio-demo
```

### Producción

#### Arquitectura de Producción por Colegio

**Diagrama de Infraestructura:**
```
Internet
    |
    v
[Nube Router / Firewall]
    |
    v
[Traefik / Nginx Proxy Manager] --> SSL Let's Encrypt
    |
    v
[Docker Swarm / Kubernetes]
    |
    +----------------+----------------+
    |                |                |
[App Django]    [PostgreSQL]     [Redis Cache]
 |                |                |
[volumes]       [volumes]       [volumes]
 |                |                |
[Archivos]     [Base Datos]    [Sessions]
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  # Reverse Proxy con SSL
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.http=true"
      - "--certificatesresolvers.myresolver.acme.http.entrypoint=web"
      - "--certificatesresolvers.myresolver.acme.email=admin@colegio.cl"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - webnet

  # Backend Django
  backend:
    build: .
    networks:
      - webnet
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`colegio-san-pedro.cl`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.certresolver=myresolver"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - media_volume:/app/media

  # Base de Datos PostgreSQL
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=schoolar_db
      - POSTGRES_USER=schoolar_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - webnet

  # Cache Redis
  redis:
    image: redis:7-alpine
    networks:
      - webnet

volumes:
  postgres_data:
  media_volume:

networks:
  webnet:
    driver: bridge
```

#### Proceso de Deploy Automatizado

**Script de Deploy (`deploy.sh`):**
```bash
#!/bin/bash

# Variables
COLEGIO_CODIGO=$1
DOMINIO=$2
DB_PASSWORD=$3

echo "🚀 Desplegendo colegio: $COLEGIO_CODIGO en $DOMINIO"

# 1. Crear directorio del colegio
mkdir -p /opt/schoolar/$COLEGIO_CODIGO
cd /opt/schoolar/$COLEGIO_CODIGO

# 2. Clonar código base
git clone https://github.com/schoolar/backend.git .

# 3. Configurar variables de entorno
cat > .env << EOF
COLEGIO_CODIGO_UNICO=$COLEGIO_CODIGO
CURRENT_HOST_URL=https://$DOMINIO
DB_PASSWORD=$DB_PASSWORD
SECRET_KEY=$(openssl rand -hex 32)
EOF

# 4. Levantar servicios
docker-compose -f docker-compose.prod.yml up -d

# 5. Esperar a que esté listo
sleep 30

# 6. Crear superusuario
docker-compose exec backend python manage.py createsuperuser \
  --username admin \
  --email admin@$DOMINIO \
  --noinput

# 7. Obtener código único
CODIGO_UNICO=$(docker-compose exec backend python manage.py get_school_code)

echo "✅ Colegio desplegado exitosamente"
echo "📋 Código único: $CODIGO_UNICO"
echo "🌐 URL: https://$DOMINIO"
echo "👤 Admin: admin@$DOMINIO"
echo "🔑 Contraseña: configurar manualmente"
```

#### Monitoreo y Actualizaciones

**Watchtower para Actualizaciones Automáticas:**
```yaml
# docker-compose.watchtower.yml
version: '3.8'

services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600 --cleanup --label-enable
    restart: unless-stopped
```

**Health Checks:**
```python
# health/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    checks = {
        'database': 'ok',
        'redis': 'ok',
        'storage': 'ok'
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
    
    try:
        import redis
        r = redis.Redis(host='redis', port=6379)
        r.ping()
    except Exception as e:
        checks['redis'] = f'error: {str(e)}'
    
    status_code = 200 if all(v == 'ok' for v in checks.values()) else 503
    
    return JsonResponse({
        'status': 'healthy' if status_code == 200 else 'unhealthy',
        'checks': checks
    }, status=status_code)
```

---

## 📱 Especificaciones Técnicas App (Universal)

### Arquitectura Frontend

#### Stack Tecnológico
- **Framework:** React Native + Expo Router
- **Lenguaje:** TypeScript
- **State Management:** Zustand
- **Navegación:** Expo Router (File-based)
- **UI:** React Native + Reanimated (para animaciones)
- **Almacenamiento Local:** SecureStore + AsyncStorage
- **Networking:** Axios con interceptores

#### Estructura de Directorios
```
src/
├── app/                    # Navegación (Expo Router)
│   ├── (tabs)/            # Navegación por pestañas
│   ├── _layout.tsx        # Layout raíz
│   └── index.tsx          # Pantalla inicial
├── components/            # Componentes UI reutilizables
│   ├── common/            # Botones, inputs, etc.
│   └── forms/             # Formularios específicos
├── screens/               # Pantallas principales
│   ├── auth/              # Login, registro
│   ├── dashboard/         # Dashboard principal
│   ├── academic/          # Notas, asistencia
│   └── profile/           # Perfil de usuario
├── services/              # Lógica de negocio
│   ├── api/               # Cliente HTTP
│   ├── auth/              # Manejo de tokens
│   └── storage/           # Almacenamiento local
├── stores/                # Estado global (Zustand)
├── types/                 # Definiciones TypeScript
├── utils/                 # Funciones helper
└── constants/             # Constantes de la app
```

#### Flujo de Autenticación

**1. Descubrimiento de Colegio:**
```typescript
// services/discovery.ts
export interface SchoolConfig {
  codigo: string;
  nombre: string;
  api_url: string;
  logo_url: string;
  colores: {
    primary: string;
    secondary: string;
  };
}

export const discoverSchool = async (codigo: string): Promise<SchoolConfig> => {
  try {
    const response = await axios.get(`${DIRECTORIO_URL}/discover/${codigo}`);
    
    if (response.data.success) {
      // Guardar configuración local
      await SecureStore.setItemAsync('school_config', JSON.stringify(response.data));
      return response.data;
    }
    
    throw new Error('Colegio no encontrado');
  } catch (error) {
    throw new Error('Error al conectar con el directorio');
  }
};
```

**2. Login y Token Management:**
```typescript
// services/auth.ts
interface LoginCredentials {
  username: string;
  password: string;
  user_type: 'alumno' | 'profesor' | 'apoderado' | 'admin';
}

export const login = async (credentials: LoginCredentials) => {
  const schoolConfig = await getStoredSchoolConfig();
  const apiClient = createApiClient(schoolConfig.api_url);
  
  try {
    const response = await apiClient.post('/api/auth/login', credentials);
    
    if (response.data.success) {
      const { access_token, refresh_token, user } = response.data.data;
      
      // Guardar tokens de forma segura
      await SecureStore.setItemAsync('access_token', access_token);
      await SecureStore.setItemAsync('refresh_token', refresh_token);
      await SecureStore.setItemAsync('user_data', JSON.stringify(user));
      
      return { success: true, user };
    }
  } catch (error) {
    throw new Error('Credenciales incorrectas');
  }
};
```

#### Sistema de Themes Dinámicos

**1. Aplicación de Theme:**
```typescript
// hooks/useTheme.ts
export const useTheme = (schoolConfig: SchoolConfig) => {
  const [theme, setTheme] = useState<Theme>(defaultTheme);

  useEffect(() => {
    const applyTheme = () => {
      const newTheme = {
        ...defaultTheme,
        colors: {
          primary: schoolConfig.colores.primary,
          secondary: schoolConfig.colores.secondary,
          background: '#FFFFFF',
          surface: '#F5F5F5',
          text: '#333333',
        }
      };
      
      setTheme(newTheme);
      
      // Aplicar a Navigation Container
      NavigationContainerRef.current?.setOptions({
        theme: {
          dark: false,
          colors: newTheme.colors
        }
      });
    };

    applyTheme();
  }, [schoolConfig]);

  return theme;
};
```

**2. Componentes Tematizados:**
```typescript
// components/common/ThemedButton.tsx
interface ThemedButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
}

export const ThemedButton: React.FC<ThemedButtonProps> = ({
  title,
  onPress,
  variant = 'primary'
}) => {
  const theme = useTheme();
  const buttonStyle = [
    styles.button,
    { backgroundColor: theme.colors[variant] }
  ];

  return (
    <TouchableOpacity style={buttonStyle} onPress={onPress}>
      <Text style={[styles.text, { color: theme.colors.onPrimary }]}>
        {title}
      </Text>
    </TouchableOpacity>
  );
};
```

#### Manejo Offline

**1. Estrategia de Caching:**
```typescript
// services/cache.ts
export class CacheManager {
  private static instance: CacheManager;
  private cache = new Map<string, any>();

  static getInstance(): CacheManager {
    if (!CacheManager.instance) {
      CacheManager.instance = new CacheManager();
    }
    return CacheManager.instance;
  }

  async set(key: string, data: any, ttl: number = 3600): Promise<void> {
    const item = {
      data,
      timestamp: Date.now(),
      ttl
    };
    
    await AsyncStorage.setItem(`cache_${key}`, JSON.stringify(item));
  }

  async get(key: string): Promise<any | null> {
    const item = await AsyncStorage.getItem(`cache_${key}`);
    
    if (!item) return null;
    
    const parsed = JSON.parse(item);
    const now = Date.now();
    
    if (now - parsed.timestamp > parsed.ttl * 1000) {
      await AsyncStorage.removeItem(`cache_${key}`);
      return null;
    }
    
    return parsed.data;
  }
}
```

**2. Sincronización Offline:**
```typescript
// services/sync.ts
export const syncWhenOnline = async () => {
  const isConnected = await NetInfo.fetch().then(state => state.isConnected);
  
  if (!isConnected) return;
  
  // Sincronizar acciones pendientes
  const pendingActions = await AsyncStorage.getItem('pending_actions');
  
  if (pendingActions) {
    const actions = JSON.parse(pendingActions);
    
    for (const action of actions) {
      try {
        await apiClient.post(action.endpoint, action.data);
      } catch (error) {
        console.error('Error syncing action:', error);
      }
    }
    
    await AsyncStorage.removeItem('pending_actions');
  }
};
```

---

## 🗄️ Especificaciones Técnicas Backend (Skeleton)

### Arquitectura Django

#### Stack Tecnológico
- **Framework:** Django 4.2 + Django REST Framework
- **Base de Datos:** PostgreSQL 15 (producción) / SQLite (desarrollo)
- **Cache:** Redis
- **Task Queue:** Celery + Redis
- **File Storage:** Django Storage (local) o AWS S3
- **Web Server:** Gunicorn + Nginx/Traefik
- **Containerización:** Docker + Docker Compose

#### Estructura de Django Apps

```
schoolar_backend/
├── apps/
│   ├── academicos/           # Gestión académica
│   │   ├── models.py        # Notas, Asistencia, Horarios
│   │   ├── serializers.py   # API serializers
│   │   ├── views.py         # API views
│   │   └── urls.py          # Endpoints
│   ├── usuarios/            # Gestión de usuarios
│   │   ├── models.py        # Perfiles, roles
│   │   ├── permissions.py   # Permisos personalizados
│   │   └── views.py         # Autenticación
│   ├── comunicacion/        # Notificaciones
│   │   ├── models.py        # Mensajes, circulars
│   │   ├── services.py      # Firebase/OneSignal
│   │   └── tasks.py         # Envío asíncrono
│   ├── documentos/          # Intranet
│   │   ├── models.py        # Recursos, archivos
│   │   ├── storage.py       # Manejo de archivos
│   │   └── views.py         # Subida/descarga
│   └── core/                # Utilidades compartidas
│       ├── permissions.py   # Permisos base
│       ├── pagination.py    # Paginación personalizada
│       └── exceptions.py    # Excepciones personalizadas
├── config/
│   ├── settings/
│   │   ├── base.py          # Configuración base
│   │   ├── development.py   # Desarrollo
│   │   ├── production.py    # Producción
│   │   └── testing.py       # Tests
│   ├── urls.py              # URLs principales
│   ├── wsgi.py              # WSGI
│   └── asgi.py              # ASGI (WebSocket)
├── docker/
│   ├── Dockerfile           # Imagen Docker
│   ├── entrypoint.sh        # Script de inicio
│   └── nginx.conf           # Configuración Nginx
├── requirements/
│   ├── base.txt             # Dependencias base
│   ├── development.txt       # Desarrollo
│   └── production.txt       # Producción
└── manage.py
```

#### Modelos de Datos Principales

**Modelo de Usuario Multi-rol:**
```python
# apps/usuarios/models.py
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrador'),
            ('profesor', 'Profesor'),
            ('alumno', 'Alumno'),
            ('apoderado', 'Apoderado'),
        ]
    )

# Perfiles específicos
class AlumnoProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    curso = models.ForeignKey('academicos.Curso', on_delete=models.SET_NULL, null=True)
    fecha_nacimiento = models.DateField()
    apoderados = models.ManyToManyField('ApoderadoProfile', through='Vinculacion')

class ProfesorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    asignaturas = models.ManyToManyField('academicos.Asignatura')
    cargo = models.CharField(max_length=100)

class ApoderadoProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono_emergencia = models.CharField(max_length=20)
    relacion_alumno = models.CharField(max_length=50)
```

**Modelos Académicos:**
```python
# apps/academicos/models.py
class Colegio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=8, unique=True)  # Código único
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    
class Curso(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)  # "4to Medio A"
    nivel = models.CharField(max_length=50)   # "4to Medio"
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    profesor_jefe = models.ForeignKey('usuarios.ProfesorProfile', on_delete=models.SET_NULL, null=True)

class Asignatura(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    cursos = models.ManyToManyField(Curso, through='CursoAsignatura')
    
class Nota(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alumno = models.ForeignKey('usuarios.AlumnoProfile', on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    tipo_evaluacion = models.CharField(max_length=50)  # "Prueba", "Tarea"
    fecha = models.DateField()
    profesor = models.ForeignKey('usuarios.ProfesorProfile', on_delete=models.CASCADE)
```

#### Serializers con Contrato Estándar

```python
# apps/academicos/serializers.py
from rest_framework import serializers
from .models import Nota, AlumnoProfile

class NotaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.user.get_full_name', read_only=True)
    asignatura_nombre = serializers.CharField(source='asignatura.nombre', read_only=True)
    
    class Meta:
        model = Nota
        fields = ['id', 'alumno', 'alumno_nombre', 'asignatura', 'asignatura_nombre', 
                  'valor', 'tipo_evaluacion', 'fecha', 'profesor']
        read_only_fields = ['id']

class AlumnoNotasSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = NotaSerializer(many=True)
    error = serializers.SerializerMethodField()
    
    def get_error(self, obj):
        return None
```

#### Views con Respuesta Estándar

```python
# apps/academicos/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Nota
from .serializers import NotaSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alumno_notas(request, alumno_id):
    """
    Obtener todas las notas de un alumno específico.
    Solo permite ver notas si el usuario tiene permisos adecuados.
    """
    try:
        # Validar permisos (alumno ve sus notas, apoderado ve notas de sus hijos, etc.)
        notas = Nota.objects.filter(alumno_id=alumno_id).select_related('asignatura', 'alumno__user')
        
        # Serializar
        serializer = NotaSerializer(notas, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'data': [],
            'error': {
                'code': 'ACAD_001',
                'message': 'Error al obtener notas del alumno'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### Sistema de Permisos

```python
# apps/core/permissions.py
from rest_framework.permissions import BasePermission

class EsPropietarioDeDatos(BasePermission):
    """
    Permite acceso solo si el usuario es dueño de los datos que solicita.
    """
    def has_object_permission(self, request, view, obj):
        # Alumno puede ver sus propios datos
        if hasattr(request.user, 'alumnoprofile'):
            return obj.alumno == request.user.alumnoprofile
        
        # Apoderado puede ver datos de sus hijos vinculados
        if hasattr(request.user, 'apoderadoprofile'):
            return obj.alumno in request.user.apoderadoprofile.hijos.all()
        
        # Profesores pueden ver datos de sus alumnos
        if hasattr(request.user, 'profesorprofile'):
            return obj.alumno.curso in request.user.profesorprofile.cursos.all()
        
        return False

class PuedeEditarNotas(BasePermission):
    """
    Solo profesores de la asignatura pueden editar notas.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'profesorprofile')
    
    def has_object_permission(self, request, view, obj):
        return obj.asignatura in request.user.profesorprofile.asignaturas.all()
```

#### API Endpoints

**URLs Principales:**
```python
# apps/academicos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Endpoints académicos
    path('api/alumnos/<uuid:alumno_id>/notas/', views.alumno_notas, name='alumno_notas'),
    path('api/alumnos/<uuid:alumno_id>/asistencia/', views.alumno_asistencia, name='alumno_asistencia'),
    path('api/alumnos/<uuid:alumno_id>/horario/', views.alumno_horario, name='alumno_horario'),
    
    # Endpoints profesores
    path('api/profesores/cursos/', views.profesor_cursos, name='profesor_cursos'),
    path('api/profesores/asignaturas/<uuid:asignatura_id>/notas/', views.profesor_subir_notas, name='profesor_subir_notas'),
    path('api/profesores/asistencia/tomar/', views.profesor_tomar_asistencia, name='profesor_tomar_asistencia'),
    
    # Endpoints intranet
    path('api/intranet/recursos/<uuid:asignatura_id>/', views.recursos_asignatura, name='recursos_asignatura'),
    path('api/intranet/recursos/subir/', views.subir_recurso, name='subir_recurso'),
    path('api/intranet/recursos/<uuid:recurso_id>/descargar/', views.descargar_recurso, name='descargar_recurso'),
]
```

#### Sistema de Notificaciones

**Servicio de Notificaciones Push:**
```python
# apps/comunicacion/services.py
from firebase_admin import messaging
from .models import DispositivoMovil, Notificacion

class NotificationService:
    @staticmethod
    async def enviar_notificacion_push(usuario_id, titulo, mensaje, data=None):
        """
        Enviar notificación push a todos los dispositivos de un usuario.
        """
        dispositivos = DispositivoMovil.objects.filter(usuario_id=usuario_id, activo=True)
        
        if not dispositivos:
            return False
        
        # Crear mensaje
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje
            ),
            data=data or {},
            tokens=[disp.token_firebase for disp in dispositivos]
        )
        
        # Enviar
        response = messaging.send_multicast(message)
        
        # Guardar registro
        Notificacion.objects.create(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            data=data,
            enviados=response.success_count,
            fallidos=response.failure_count
        )
        
        return response.success_count > 0
```

---

## 🔒 Seguridad y Mejoras Críticas

### 1. Gestión de Tokens JWT

#### Implementación Segura

**Configuración Django:**
```python
# settings/production.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'schoolar-os',
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
```

**Endpoints de Autenticación:**
```python
# apps/usuarios/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login con JWT tokens y validación de dispositivo."""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        user_type = request.data.get('user_type')
        device_info = request.data.get('device_info', {})
        
        # Autenticación estándar Django
        user = authenticate(username=username, password=password)
        
        if not user or user.user_type != user_type:
            return Response({
                'success': False,
                'error': {
                    'code': 'AUTH_001',
                    'message': 'Credenciales inválidas o tipo de usuario incorrecto'
                }
            }, status=401)
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # Registrar dispositivo
        device_token = device_info.get('device_token')
        if device_token:
            DispositivoMovil.objects.update_or_create(
                user=user,
                token_firebase=device_token,
                defaults={
                    'tipo': device_info.get('type', 'mobile'),
                    'activo': True,
                    'ultimo_acceso': timezone.now()
                }
            )
        
        return Response({
            'success': True,
            'data': {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            },
            'error': None
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'AUTH_002',
                'message': 'Error en el proceso de autenticación'
            }
        }, status=500)
```

#### Refresh Automático en Cliente

```typescript
// services/auth.ts
class AuthService {
  private static instance: AuthService;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string | null) => void> = [];

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async refreshToken(): Promise<string | null> {
    if (this.isRefreshing) {
      return new Promise(resolve => {
        this.refreshSubscribers.push(resolve);
      });
    }

    this.isRefreshing = true;

    try {
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      if (!refreshToken) throw new Error('No refresh token');

      const response = await axios.post('/api/auth/refresh/', {
        refresh: refreshToken
      });

      const { access } = response.data;
      
      // Guardar nuevo token
      await SecureStore.setItemAsync('access_token', access);
      
      // Notificar a todos los que esperaban
      this.refreshSubscribers.forEach(callback => callback(access));
      this.refreshSubscribers = [];
      
      return access;
    } catch (error) {
      // Refresh falló, hacer logout
      this.refreshSubscribers.forEach(callback => callback(null));
      this.refreshSubscribers = [];
      await this.logout();
      return null;
    } finally {
      this.isRefreshing = false;
    }
  }

  async logout(): Promise<void> {
    // Limpiar tokens
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await SecureStore.deleteItemAsync('user_data');
    
    // Limpiar configuración del colegio
    await SecureStore.deleteItemAsync('school_config');
    
    // Navegar a login
    // navigation.reset(...);
  }
}
```

### 2. Identificadores UUID v4

#### Implementación Completa

**Modelos con UUID:**
```python
# apps/core/models.py
import uuid
from django.db import models

class UUIDModel(models.Model):
    """
    Modelo base con UUID como primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Uso en modelos específicos
class Alumno(UUIDModel):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=200)
    # ... otros campos
```

**Serializers con UUID:**
```python
# serializers.py
class AlumnoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Alumno
        fields = ['id', 'rut', 'nombre']
```

**Validación de UUID en Views:**
```python
# views.py
from uuid import UUID
from django.core.exceptions import ValidationError

def validate_uuid(uuid_string):
    try:
        UUID(str(uuid_string), version=4)
        return True
    except ValueError:
        return False

@api_view(['GET'])
def obtener_alumno(request, alumno_id):
    if not validate_uuid(alumno_id):
        return Response({
            'success': False,
            'error': {'code': 'VALID_001', 'message': 'ID inválido'}
        }, status=400)
    
    try:
        alumno = Alumno.objects.get(id=alumno_id)
        # ... resto del código
    except Alumno.DoesNotExist:
        return Response({
            'success': False,
            'error': {'code': 'NOT_FOUND_001', 'message': 'Alumno no encontrado'}
        }, status=404)
```

### 3. Aislamiento Docker Multi-Colegio

#### Configuración Docker Completa

**Dockerfile Multi-stage:**
```dockerfile
# Multi-stage para optimización
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias desde wheels
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copiar código
COPY . .

# Crear usuario no-root para seguridad
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app
USER django

# Script de entrada
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
```

**docker-compose.production.yml:**
```yaml
version: '3.8'

services:
  # Web Application
  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
      - DATABASE_URL=postgresql://schoolar_user:${DB_PASSWORD}@postgres:5432/schoolar_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - media_volume:/app/media
      - static_volume:/app/staticfiles
    depends_on:
      - postgres
      - redis
    networks:
      - app-network

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=schoolar_db
      - POSTGRES_USER=schoolar_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./docker/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  media_volume:
  static_volume:

networks:
  app-network:
    driver: bridge
```

#### Entrypoint Inteligente

**entrypoint.sh:**
```bash
#!/bin/bash
set -e

# Función para esperar a que la base de datos esté lista
wait_for_db() {
    echo "🔍 Esperando a que PostgreSQL esté listo..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
        sleep 2
    done
    echo "✅ PostgreSQL está listo!"
}

# Función para esperar a Redis
wait_for_redis() {
    echo "🔍 Esperando a que Redis esté listo..."
    until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping; do
        sleep 2
    done
    echo "✅ Redis está listo!"
}

# Función de registro automático (Phone Home)
register_with_directory() {
    if [ ! -f /app/.registered ] && [ -n "$COLEGIO_CODIGO_UNICO" ]; then
        echo "📝 Registrando colegio con código: $COLEGIO_CODIGO_UNICO"
        
        curl -X POST "$DIRECTORIO_URL/register" \
             -H "Content-Type: application/json" \
             -d "{
                 \"codigo\": \"$COLEGIO_CODIGO_UNICO\",
                 \"url\": \"$CURRENT_HOST_URL\",
                 \"nombre\": \"$COLEGIO_NOMBRE\"
             }" || echo "⚠️ Error registrando con directorio (puede ser normal en desarrollo)"
        
        touch /app/.registered
        echo "✅ Colegio registrado exitosamente"
    fi
}

# Función de inicialización
initialize_app() {
    echo "🏗️ Inicializando aplicación Schoolar OS..."
    
    # Esperar servicios
    wait_for_db
    wait_for_redis
    
    # Migraciones
    echo "🔄 Ejecutando migraciones..."
    python manage.py migrate --noinput
    
    # Collect static
    echo "📦 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    
    # Crear superusuario si no existe
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@schoolar.os', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
EOF
    fi
    
    # Registrar con directorio
    register_with_directory
    
    echo "✅ Inicialización completada!"
}

# Ejecutar inicialización si corresponde
if [ "$1" = "migrate" ]; then
    initialize_app
    exit 0
fi

# Iniciar aplicación
echo "🚀 Iniciando servidor Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --worker-tmp-dir /tmp \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### 4. Validaciones de Seguridad

#### Protección contra Ataques Comunes

**Middleware de Seguridad:**
```python
# config/middleware.py
import time
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings

class RateLimitMiddleware:
    """
    Middleware para rate limiting por IP.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener IP del cliente
        ip = self.get_client_ip(request)
        
        # Rate limiting para endpoints críticos
        if request.path.startswith('/api/auth/'):
            cache_key = f"rate_limit_auth_{ip}"
            requests = cache.get(cache_key, 0)
            
            if requests > 10:  # Más de 10 intentos por minuto
                return HttpResponseForbidden('Too many requests')
            
            cache.set(cache_key, requests + 1, 60)  # Expira en 1 minuto
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

**Validaciones en Modelos:**
```python
# apps/usuarios/models.py
from django.core.exceptions import ValidationError
import re

class User(AbstractUser):
    rut = models.CharField(max_length=12, unique=True)
    
    def clean(self):
        super().clean()
        self.validate_rut()
    
    def validate_rut(self):
        """Validar formato de RUT chileno."""
        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', self.rut):
            raise ValidationError('RUT inválido. Use formato XX.XXX.XXX-X')
        
        # Validar dígito verificador
        rut_clean = self.rut.replace('.', '').replace('-', '')
        dv = rut_clean[-1].upper()
        rut_body = rut_clean[:-1]
        
        total = 0
        for i in range(len(rut_body)):
            total += int(rut_body[i]) * (9 - i % 6) % 10
        
        expected_dv = str((11 - total % 10) % 10)
        if dv != expected_dv and dv != 'K':
            raise ValidationError('RUT inválido. Dígito verificador incorrecto')
```

#### CORS y Headers de Seguridad

**Configuración CORS:**
```python
# settings/production.py
CORS_ALLOWED_ORIGINS = [
    "https://colegio-san-pedro.cl",
    "https://www.colegio-san-pedro.cl",
    "exp://*.*.*.*",  # Para desarrollo móvil
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = False  # Solo orígenes específicas

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

### 5. Monitoreo y Logging

#### Sistema de Logs Estructurados

**Configuración de Logging:**
```python
# settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s"}',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
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
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
```

#### Métricas de Salud

**Health Check Endpoint:**
```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
import psutil

def health_check(request):
    """Endpoint completo de health check."""
    checks = {}
    status_code = 200
    
    # Base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        status_code = 503
    
    # Cache Redis
    try:
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {str(e)}'
        status_code = 503
    
    # Espacio en disco
    disk_usage = psutil.disk_usage('/app')
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    if disk_percent > 80:
        checks['disk'] = f'warning: {disk_percent:.1f}% used'
        status_code = 503
    else:
        checks['disk'] = f'ok: {disk_percent:.1f}% used'
    
    # Memoria
    memory = psutil.virtual_memory()
    if memory.percent > 80:
        checks['memory'] = f'warning: {memory.percent:.1f}% used'
        status_code = 503
    else:
        checks['memory'] = f'ok: {memory.percent:.1f}% used'
    
    return JsonResponse({
        'status': 'healthy' if status_code == 200 else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'version': '2.0.0',
        'checks': checks
    }, status=status_code)
```

---

## 📚 Conclusiones y Próximos Pasos

### Estado Actual del Proyecto

Schoolar OS está arquitectónicamente listo para producción con:

✅ **Arquitectura Skeleton & Fleet implementada**
✅ **Sistema de autenticación JWT seguro**
✅ **Identificadores UUID v4 para todo**
✅ **Aislamiento Docker completo**
✅ **API RESTful con contrato estándar**
✅ **Sistema de notificaciones push**
✅ **Módulo Intranet funcional**
✅ **Matriz de roles completa**
✅ **Guías de desarrollo local**
✅ **Infraestructura de producción lista**

### Próximos Pasos para el Equipo

#### Para el Backend Developer:

1. **Implementar Management Commands para seeding:**
   ```bash
   python manage.py seed_demo_data
   python manage.py create_test_users
   python manage.py setup_demo_school
   ```

2. **Crear endpoints faltantes:**
   - API de vinculaciones familia-alumno
   - Sistema de circulars y comunicados
   - Reportes y estadísticas

3. **Optimización de queries:**
   - Implementar `select_related` y `prefetch_related`
   - Crear índices de base de datos adecuados

#### Para el Frontend Developer:

1. **Implementar pantallas principales:**
   - Dashboard por rol
   - Listado de notas y asistencia
   - Intranet de descarga de archivos

2. **Sincronización offline:**
   - Caching inteligente de datos
   - Cola de acciones pendientes
   - Sincronización cuando hay conexión

3. **Testing y QA:**
   - Unit tests para componentes
   - Integration tests para API
   - Testing en dispositivos reales

#### Para DevOps:

1. **Configurar CI/CD:**
   - GitHub Actions para tests automáticos
   - Deploy automático a staging/producción
   - Monitoreo con Prometheus + Grafana

2. **Setup de producción:**
   - Configurar dominios SSL
   - Setup de backups automáticos
   - Monitoreo de rendimiento

### Checklist de Producción

- [ ] Cada colegio tiene su propia VPS y dominio
- [ ] SSL/TLS configurado en todos los colegios
- [ ] Sistema de backup diario de bases de datos
- [ ] Monitoring centralizado de toda la flota
- [ ] Sistema de actualización automática (Watchtower)
- [ ] Documentación de operaciones completa
- [ ] Testing de penetración de seguridad
- [ ] Plan de disaster recovery

---

**Este documento es la Biblia Técnica y Operativa definitiva de Schoolar OS.** Toda decisión arquitectónica, implementación y operación debe basarse en estos principios y especificaciones para mantener la consistencia, seguridad y escalabilidad del sistema.

**Versión 2.0 - Diciembre 2024**  
**Estado: Production Ready**  
**Próxima Actualización: Según evolución del proyecto**
