# 📋 Plan de Remediación - Schoolar OS

> **Basado en Auditoría de Código**  
> Generado: 2024-12-18

---

## 🔥 Sprint 1: Seguridad Crítica (Bloqueante)

| # | Tarea | Esfuerzo | Impacto |
|---|-------|----------|---------|
| 1 | Agregar rate limiting a API JWT | 1h | Previene fuerza bruta |
| 2 | Agregar `token_blacklist` a INSTALLED_APPS | 15min | Habilita revocación tokens |
| 3 | Remover `id` de UserSerializer | 15min | Cumple política UUIDs |
| 4 | Eliminar `CORS_ALLOW_ALL_ORIGINS` | 15min | Previene robo de datos |
| 5 | Crear `TareaForm` con validación | 2h | Previene XSS almacenado |

**Total:** ~4 horas

---

## 🔧 Sprint 2: Rendimiento y Estabilidad

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 1 | Optimizar N+1 en `ApoderadoPupilosView` | 3h |
| 2 | Agregar `select_for_update()` en entregas | 1h |
| 3 | Usar `secrets` en lugar de `random` | 15min |
| 4 | Agregar índices a campos filtrados | 1h |

**Total:** ~5 horas

---

## 📋 Sprint 3: Calidad y Mantenibilidad

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 1 | Tests para endpoints críticos de API | 4h |
| 2 | Permission classes DRY | 2h |
| 3 | Mover imports a nivel de módulo | 1h |
| 4 | Logging de eventos de seguridad | 2h |

**Total:** ~9 horas

---

## 📊 Resumen

| Sprint | Prioridad | Horas | Estado |
|--------|-----------|-------|--------|
| Sprint 1 | 🔴 Crítica | 4h | Pendiente |
| Sprint 2 | 🟠 Alta | 5h | Pendiente |
| Sprint 3 | 🟡 Media | 9h | Pendiente |

**Total estimado:** 18 horas de desarrollo
