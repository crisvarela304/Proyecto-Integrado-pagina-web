from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from usuarios.models import PerfilUsuario
from academico.models import Calificacion, Asistencia, Examen, Curso, Asignatura
from documentos.models import Documento

class Command(BaseCommand):
    help = 'Configura grupo y permisos para profesores y los hace staff'

    def handle(self, *args, **options):
        self.stdout.write("Configurando grupo y permisos para Profesores...")

        # 1. Crear o obtener el grupo "Profesores"
        grupo_profesores, created = Group.objects.get_or_create(name='Profesores')
        if created:
            self.stdout.write(self.style.SUCCESS("Grupo 'Profesores' creado."))
        else:
            self.stdout.write("Grupo 'Profesores' ya existe.")

        # 2. Definir permisos requeridos
        permisos_config = [
            # Academico
            ('academico', 'calificacion', ['add_calificacion', 'change_calificacion', 'view_calificacion']),
            ('academico', 'asistencia', ['add_asistencia', 'change_asistencia', 'view_asistencia']),
            ('academico', 'examen', ['add_examen', 'change_examen', 'view_examen']),
            ('academico', 'curso', ['view_curso']),
            ('academico', 'asignatura', ['view_asignatura']),
            # Documentos
            ('documentos', 'documento', ['add_documento', 'change_documento', 'view_documento', 'delete_documento']),
            # Usuarios (Necesario para autocomplete)
            ('auth', 'user', ['view_user']),
        ]

        permisos_a_asignar = []
        for app_label, model_name, codenames in permisos_config:
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                for codename in codenames:
                    try:
                        permiso = Permission.objects.get(content_type=content_type, codename=codename)
                        permisos_a_asignar.append(permiso)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Permiso '{codename}' no encontrado para {model_name}."))
            except ContentType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"ContentType no encontrado para {app_label}.{model_name}"))

        # 3. Asignar permisos al grupo
        grupo_profesores.permissions.set(permisos_a_asignar)
        self.stdout.write(f"Se asignaron {len(permisos_a_asignar)} permisos al grupo 'Profesores'.")

        # 4. Actualizar usuarios profesores
        profesores_perfil = PerfilUsuario.objects.filter(tipo_usuario='profesor')
        count = 0
        for perfil in profesores_perfil:
            user = perfil.user
            changed = False
            
            if not user.is_staff:
                user.is_staff = True
                changed = True
            
            if not user.groups.filter(name='Profesores').exists():
                user.groups.add(grupo_profesores)
                changed = True
            
            if changed:
                user.save()
                self.stdout.write(f"Usuario {user.username} actualizado.")
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. {count} profesores actualizados."))
