# Schoolar OS - Backend Context

## 🎯 Modelo de Negocio
```
Nos contratan → Instalamos web (dominio único) → VPS por colegio → Código único → App universal se conecta
```

**Objetivo**: Sistema escolar distribuido SaaS donde cada colegio tiene su propia instancia aislada.

---

## 🏗️ Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────┐
│              DIRECTORIO CENTRAL (api.schoolar-os.com)       │
│    Base de datos maestra de códigos + URLs + branding       │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲
    Phone Home     Phone Home     Phone Home
         │              │              │
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ VPS Colegio │ │ VPS Colegio │ │ VPS Colegio │
│ San Pedro   │ │ Los Andes   │ │ Santa María │
│ PostgreSQL  │ │ PostgreSQL  │ │ PostgreSQL  │
│ COLE-SP-24  │ │ COLE-LA-24  │ │ COLE-SM-24  │
└─────────────┘ └─────────────┘ └─────────────┘
         ▲              ▲              ▲
         └──────────────┼──────────────┘
                        │
            ┌───────────────────────┐
            │   APP UNIVERSAL 📱    │
            │  (Play Store única)   │
            │  Se "transforma" con  │
            │  el código del cole   │
            └───────────────────────┘
```

---

## 📱 La App "Camaleón" - Cómo Funciona

1. **Usuario baja App** → Cascarón vacío (sin logo, sin colores, sin servidor)
2. **Ingresa código** → `COLE-SP-24`
3. **App pregunta al Directorio Central** → "¿Dónde está COLE-SP-24?"
4. **Directorio responde** → URL + colores + logo
5. **App se transforma** → Se "pinta" con branding del colegio
6. **Conexión directa** → Desde ahora habla SOLO con ese servidor

---

## 👥 Flujo de Onboarding de Usuarios

### Fase 1: Instalación (Nosotros)
```
1. Cliente firma contrato
2. Compramos dominio (colegio-ejemplo.cl)
3. Desplegamos Docker en VPS
4. Sistema genera código único (COLE-XX-24)
5. Entregamos código al Director por email
```

### Fase 2: Registro Inicial (Director)
```
1. Director abre web con dominio del colegio
2. Ingresa código único
3. Se registra como "Administrativo Alto"
4. Sistema le otorga rol de SuperUsuario
```

### Fase 3: Estructura Organizacional
```
Director/Admin Alto
    │
    ├── Crea Administrativos Bajos (inspectores, secretarios)
    ├── Aprueba Profesores (se auto-registran)
    └── Aprueba Alumnos (se auto-registran)
            │
            └── Alumno invita a su Apoderado
```

### Jerarquía de Roles
| Rol | Nivel | Puede Aprobar |
|-----|-------|---------------|
| `superusuario` | Nosotros (Dios) | Todo |
| `admin_alto` | Director, Subdirector | Admins bajos, Profesores, Alumnos |
| `admin_bajo` | Inspector, Secretario | Consultas, Reportes |
| `profesor` | Docente | Notas, Asistencia |
| `estudiante` | Alumno | Invitar apoderado |
| `apoderado` | Padre/Tutor | Solo lectura |

---

## 🔑 Protocolo "Phone Home" (Auto-Registro)

### Al desplegar un colegio nuevo:
```python
# 1. VPS arranca el Docker
# 2. El sistema lee la variable de entorno
CURRENT_HOST_URL = "https://colegio-san-pedro.cl"

# 3. Genera/recupera código único
school_code = "COLE-SP-24"

# 4. POST al Directorio Central
POST api.schoolar-os.com/register
{
    "code": "COLE-SP-24",
    "url": "https://colegio-san-pedro.cl",
    "name": "Colegio San Pedro",
    "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
    "logo_url": "https://colegio-san-pedro.cl/static/logo.png"
}

# 5. Directorio guarda en su BD
# 6. Ahora cualquier App puede encontrar este colegio
```

---

## 🛠️ Stack Técnico

### Backend (Por Colegio)
- **Framework**: Django REST Framework
- **Auth**: SimpleJWT (15 min access / 7 días refresh)
- **DB Dev**: SQLite
- **DB Prod**: PostgreSQL
- **WSGI**: Gunicorn
- **Container**: Docker + Watchtower

### Frontend App
- **Framework**: React Native + Skia
- **Estado**: Zustand / Redux
- **HTTP**: Axios
- **Almacenamiento**: AsyncStorage (código + token)

### Directorio Central
- **Rol**: Registro de colegios + Discovery
- **Endpoints**:
  - `POST /register` - Phone Home
  - `GET /discover/{code}` - App busca colegio
  - `GET /health` - Estado de la flota

---

## ⚡ Reglas de Oro

### 1. IDs
> **ESTRICTO**: UUID v4 para IDs públicos. **NUNCA** Integers.

### 2. Seguridad
> Rate Limiting en login. Filtrar por scope de usuario/colegio.

### 3. Performance
> Zero N+1 Queries en Serializers.

### 4. API
> Envelope estándar Success/Error.

---

## 📅 Cronograma de Operación

| Evento | Responsable | Acción |
|--------|-------------|--------|
| Día 0 (Venta) | Nosotros | VPS + Dominio + Deploy + Código |
| Mensual | Nosotros | Health checks del Directorio |
| Hotfix | Nosotros | Push a Git → Watchtower actualiza flota |

---

## 🎯 Resumen para la IA

Cuando desarrolles para Schoolar OS recuerda:
- Es un sistema **multi-tenant físico** (1 VPS = 1 colegio)
- La App es **universal** pero se "personaliza" con el código
- El **Directorio Central** es el cerebro que conecta App ↔ Backend
- Los usuarios se **auto-registran** y son **aprobados** por jerarquía
- Todo usa **UUIDs**, nunca IDs enteros expuestos
