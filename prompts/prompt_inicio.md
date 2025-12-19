# Prompt de Inicio para Desarrollo

## 📋 Prompt Base (Copiar al inicio de cada tarea)

```
Lee backend_context.json. Actúa como el Arquitecto definido ahí.

TAREA: [Describe aquí lo que necesitas]

REQUISITOS:
- Usa UUIDs para todos los IDs públicos
- Asegura que el código sea compatible con el protocolo 'Phone Home'
- Genera el código completo: Model → Serializer → View → URL
- Incluye tests básicos

CONTEXTO ADICIONAL (si aplica):
- [Información relevante del feature]
```

---

## 🔍 Prompt de Revisión (Enviar después de recibir el código)

```
Analiza este código que acabas de generar. Busca:
1. Condiciones de carrera
2. Renders innecesarios
3. Problemas de seguridad
4. N+1 queries
5. IDs expuestos como Integers
6. Falta de validación de permisos

Sé despiadado. No asumas que está correcto.
```

---

## 📝 Ejemplos de Tareas

### Crear nuevo modelo
```
Lee backend_context.json. Actúa como el Arquitecto definido ahí.

TAREA: Crear el modelo de Asistencia con los siguientes campos:
- Estudiante (FK)
- Fecha
- Estado (presente, ausente, tardanza, justificado)
- Observaciones (opcional)

REQUISITOS:
- Usa UUIDs
- Genera: Model → Serializer → View → URL
- Solo profesores pueden registrar asistencia
- Solo se puede registrar una vez por día por estudiante
```

### Crear endpoint de API
```
Lee backend_context.json. Actúa como el Arquitecto definido ahí.

TAREA: Crear endpoint GET /api/v1/notas/ que retorne las notas del estudiante autenticado

REQUISITOS:
- Usa UUIDs
- Filtrar por request.user (solo ver propias notas)
- Incluir información del curso y evaluación
- Paginación de 20 items
- Optimizar para evitar N+1 queries
```

### Crear vista/pantalla
```
Lee backend_context.json. Actúa como el Arquitecto definido ahí.

TAREA: Crear la pantalla de notas para el panel del estudiante

REQUISITOS:
- Mostrar tabla con: Curso, Evaluación, Nota, Fecha
- Filtro por curso
- Ordenar por fecha descendente
- Diseño responsive con CSS existente
```

---

## ⚠️ Recordatorios Importantes

1. **Siempre verificar** que el código generado use UUIDs
2. **Siempre verificar** que no haya N+1 queries
3. **Siempre verificar** filtrado por usuario/organización
4. **Siempre pedir** revisión despiadada después de generar
