# Instrucciones de Implementación del Módulo de Mensajería

## 1. Ejecutar Migraciones
```bash
python manage.py makemigrations mensajeria
python manage.py migrate
```

## 2. Cargar Datos de Prueba
```bash
python manage.py loaddata mensajeria/fixtures/seed_mensajeria.json
```

## 3. Configurar Grupos de Usuarios
```bash
python manage.py shell
```

Ejecutar en el shell:
```python
from django.contrib.auth.models import Group

# Crear grupos si no existen
grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
grupo_profesor, _ = Group.objects.get_or_create(name='Profesor')
print("Grupos configurados correctamente")
```

## 4. Verificar Configuración
- Ejecutar tests: `python manage.py test mensajeria`
- Acceder a `/admin/` para ver el panel de mensajería
- Acceder a `/mensajeria/` para probar la interfaz

## 5. Asignar Usuarios a Grupos
Los usuarios del fixture ya están asignados, pero si quieres asignar otros:

```python
from django.contrib.auth.models import User

# Asignar usuario como alumno
alumno = User.objects.get(username='nuevo_alumno')
grupo_alumno = Group.objects.get(name='Alumno')
alumno.groups.add(grupo_alumno)

# Asignar usuario como profesor
profesor = User.objects.get(username='nuevo_profesor')
grupo_profesor = Group.objects.get(name='Profesor')
profesor.groups.add(grupo_profesor)
```

## 6. Configurar Directorio de Archivos
Asegurarse de que existe el directorio para archivos adjuntos:
- `media/mensajeria/adjuntos/` (se crea automáticamente)

## 7. Verificar URLS
Las URLs están configuradas en `config/urls.py`:
- `/mensajeria/` - Lista de conversaciones
- `/mensajeria/nueva/` - Nueva conversación
- `/mensajeria/<id>/` - Detalle de conversación
- `/mensajeria/<id>/enviar/` - Enviar mensaje
- `/mensajeria/<id>/eliminar/` - Eliminar conversación
- `/mensajeria/<id>/leido/` - Marcar como leído

## 8. Datos de Prueba Disponibles
Los fixtures incluyen:
- **6 estudiantes:** carlos.rodriguez, maria.gonzalez, andres.martinez, sofia.lopez, valentina.castro, benjamin.morales
- **5 profesores:** prof.gonzalez, prof.rojas, prof.lagos, prof.silva, prof.moreno
- **Contraseña para todos:** testpass123 (contraseña encriptada en el fixture)
- **5 conversaciones activas** con 17 mensajes de ejemplo

## 9. Navegación desde el Panel Principal
Los enlaces ya están configurados en el panel de usuario. Los estudiantes y profesores verán el enlace "Mensajería" en sus paneles.

## 10. Personalización Adicional
Si deseas personalizar colores, logotipos o mensajes, modifica:
- `mensajeria/templates/mensajeria/` para cambiar la interfaz
- `mensajeria/models.py` para cambiar el comportamiento
- `mensajeria/views.py` para cambiar la lógica
- `mensajeria/admin.py` para personalizar el panel de administración

¡El módulo de mensajería está completamente implementado y listo para usar!
