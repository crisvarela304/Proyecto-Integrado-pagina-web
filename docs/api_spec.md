# Schoolar OS - API REST Specification

> **Documento para el desarrollador de la App móvil**

## Base URL
```
https://[dominio-del-colegio]/api/
```

## Autenticación
La API usa **JWT (JSON Web Tokens)**. Incluir en cada request:
```
Authorization: Bearer <access_token>
```

---

## 🔐 Endpoints de Autenticación

### POST /api/auth/login/
Login del usuario. Retorna tokens JWT.

**Request:**
```json
{
  "username": "12345678-9",
  "password": "contraseña"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "12345678-9",
      "email": "estudiante@colegio.cl",
      "first_name": "Juan",
      "last_name": "Pérez",
      "perfil": {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "rut": "12.345.678-9",
        "tipo_usuario": "estudiante",
        "telefono": "+56912345678",
        "foto_perfil": null,
        "fecha_nacimiento": "2008-05-15",
        "nombre_completo": "Juan Pérez"
      }
    }
  },
  "message": "Login exitoso",
  "errors": null
}
```

**Errores:**
- `401`: Credenciales inválidas

---

### POST /api/auth/refresh/
Renovar el access token usando el refresh token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Token renovado",
  "errors": null
}
```

---

## 🎓 Endpoints de Alumno

### GET /api/alumno/me/
Retorna el perfil del alumno autenticado.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "12345678-9",
    "email": "estudiante@colegio.cl",
    "first_name": "Juan",
    "last_name": "Pérez",
    "perfil": { ... },
    "curso": {
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "nombre": "1° Medio A",
      "promedio": 5.8
    }
  },
  "message": "OK",
  "errors": null
}
```

---

### GET /api/alumno/me/notas/
Retorna las notas del alumno.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notas": [
      {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "asignatura": {
          "uuid": "...",
          "nombre": "Matemáticas",
          "codigo": "MAT"
        },
        "nota": 6.5,
        "tipo_evaluacion": "nota",
        "tipo_evaluacion_display": "Nota",
        "descripcion": "Prueba 1",
        "fecha_evaluacion": "2024-03-15",
        "semestre": "1",
        "numero_evaluacion": 1
      }
    ],
    "promedio_general": 5.8,
    "total": 15
  },
  "message": "OK",
  "errors": null
}
```

---

### GET /api/alumno/me/asistencia/
Retorna la asistencia del alumno.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "asistencia": [
      {
        "uuid": "...",
        "fecha": "2024-03-20",
        "estado": "presente",
        "estado_display": "Presente",
        "observacion": ""
      }
    ],
    "estadisticas": {
      "total_dias": 45,
      "dias_presente": 42,
      "porcentaje_asistencia": 93.3
    }
  },
  "message": "OK",
  "errors": null
}
```

---

### GET /api/alumno/me/horario/
Retorna el horario del curso del alumno.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "curso": "1° Medio A",
    "horario": [
      {
        "dia": "lunes",
        "dia_display": "Lunes",
        "hora": "1",
        "hora_display": "08:00 - 08:45",
        "asignatura": {
          "uuid": "...",
          "nombre": "Matemáticas",
          "codigo": "MAT"
        },
        "sala": "A-101"
      }
    ]
  },
  "message": "OK",
  "errors": null
}
```

---

### GET /api/alumno/me/anotaciones/
Retorna las anotaciones (hoja de vida) del alumno.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "anotaciones": [
      {
        "uuid": "...",
        "tipo": "positiva",
        "tipo_display": "Positiva (Mérito)",
        "categoria": "participacion",
        "categoria_display": "Participación en Clases",
        "observacion": "Excelente participación en debates",
        "fecha": "2024-03-15T10:30:00Z"
      }
    ],
    "resumen": {
      "positivas": 5,
      "negativas": 1
    }
  },
  "message": "OK",
  "errors": null
}
```

---

## 🔔 Endpoints de Notificaciones

### GET /api/notificaciones/
Retorna las notificaciones del usuario.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notificaciones": [
      {
        "uuid": "...",
        "tipo": "nota",
        "tipo_display": "Nueva Calificación",
        "titulo": "Nueva nota en Matemáticas",
        "mensaje": "Se ha registrado una nueva calificación",
        "url": "/academico/notas/",
        "leida": false,
        "created_at": "2024-03-20T14:30:00Z"
      }
    ],
    "no_leidas": 3
  },
  "message": "OK",
  "errors": null
}
```

---

### POST /api/notificaciones/{uuid}/leer/
Marca una notificación como leída.

**Response (200):**
```json
{
  "success": true,
  "data": null,
  "message": "Notificación marcada como leída",
  "errors": null
}
```

---

## 🏫 Endpoints de Colegio

### GET /api/colegio/discover/
**PÚBLICO** - No requiere autenticación.
Retorna información del colegio para configurar la App.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "codigo": "COLE-W1D9",
    "nombre": "Liceo Juan Bautista",
    "url": "https://liceo-juan-bautista.cl",
    "branding": {
      "logo": "https://liceo.../media/colegio/logo.png",
      "color_primario": "#1976D2",
      "color_secundario": "#424242"
    }
  },
  "message": "OK",
  "errors": null
}
```

---

## ⚠️ Formato de Errores

Todos los errores siguen este formato:

```json
{
  "success": false,
  "data": null,
  "message": "Descripción del error",
  "errors": {
    "campo": ["Mensaje de error específico"]
  }
}
```

**Códigos HTTP:**
| Código | Significado |
|--------|-------------|
| 200 | Éxito |
| 400 | Error de validación |
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | No encontrado |
| 500 | Error del servidor |

---

## 🔧 Configuración JWT

| Parámetro | Valor |
|-----------|-------|
| Access Token Lifetime | 15 minutos |
| Refresh Token Lifetime | 7 días |
| Header | `Authorization: Bearer <token>` |

---

## 📱 Flujo de la App

1. Usuario ingresa código del colegio (ej: `COLE-W1D9`)
2. App llama a `GET /api/colegio/discover/` para obtener URL y branding
3. App se conecta a la URL del colegio
4. Usuario hace login con `POST /api/auth/login/`
5. App guarda tokens y muestra interfaz según `tipo_usuario`
6. Cada 15 min, usar `POST /api/auth/refresh/` para renovar token

---

## 📚 Endpoints de Tareas (Alumno)

### GET /api/alumno/me/tareas/
Retorna las tareas del alumno separadas en pendientes y entregadas.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "pendientes": [
      {
        "uuid": "...",
        "titulo": "Ensayo sobre la Segunda Guerra Mundial",
        "descripcion": "Escribir un ensayo de 3 páginas...",
        "tipo": "trabajo",
        "tipo_display": "Trabajo de Investigación",
        "asignatura": { "uuid": "...", "nombre": "Historia", "codigo": "HIS" },
        "fecha_asignacion": "2024-03-10",
        "fecha_entrega": "2024-03-25",
        "hora_limite": "23:59:00",
        "puntaje_maximo": 100,
        "estado": "publicada",
        "estado_display": "Publicada",
        "esta_vencida": false
      }
    ],
    "entregadas": [...],
    "total_pendientes": 3
  },
  "message": "OK",
  "errors": null
}
```

---

### GET /api/alumno/me/entregas/
Retorna las entregas del alumno con calificaciones.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "entregas": [
      {
        "uuid": "...",
        "tarea": { ... },
        "fecha_entrega": "2024-03-20T14:30:00Z",
        "entrega_tardia": false,
        "puntaje": 85.0,
        "comentario_profesor": "Buen trabajo, mejorar redacción",
        "estado": "revisada",
        "estado_display": "Revisada"
      }
    ],
    "total": 5
  },
  "message": "OK",
  "errors": null
}
```

---

## 👨‍👩‍👧 Endpoints de Apoderado

### GET /api/apoderado/pupilos/
Retorna los hijos/pupilos del apoderado con resumen académico.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "pupilos": [
      {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "nombre_completo": "Juan Pérez González",
        "rut": "21.456.789-0",
        "vinculo": "Padre",
        "es_principal": true,
        "curso": "1° Medio A",
        "promedio": 5.8,
        "asistencia": 93.5
      }
    ],
    "total": 2
  },
  "message": "OK",
  "errors": null
}
```

---

## 📋 Resumen de Endpoints

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| POST | `/api/auth/login/` | ❌ | Login JWT |
| POST | `/api/auth/refresh/` | ❌ | Renovar token |
| GET | `/api/colegio/discover/` | ❌ | Info del colegio |
| GET | `/api/alumno/me/` | ✅ | Perfil del alumno |
| GET | `/api/alumno/me/notas/` | ✅ | Notas + promedio |
| GET | `/api/alumno/me/asistencia/` | ✅ | Asistencia + % |
| GET | `/api/alumno/me/horario/` | ✅ | Horario del curso |
| GET | `/api/alumno/me/anotaciones/` | ✅ | Hoja de vida |
| GET | `/api/alumno/me/tareas/` | ✅ | Tareas pendientes/entregadas |
| GET | `/api/alumno/me/entregas/` | ✅ | Entregas con notas |
| GET | `/api/notificaciones/` | ✅ | Notificaciones |
| POST | `/api/notificaciones/{uuid}/leer/` | ✅ | Marcar leída |
| GET | `/api/apoderado/pupilos/` | ✅ | Hijos del apoderado |

