from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Configura datos de ejemplo para el sistema de mensajería'

    def handle(self, *args, **kwargs):
        self.stdout.write("📊 Creando datos de ejemplo para mensajería...")
        
        try:
            # Crear grupos
            alumno_group, created = Group.objects.get_or_create(name='Alumno')
            profesor_group, created = Group.objects.get_or_create(name='Profesor')
            
            # Crear usuarios de ejemplo
            if not User.objects.filter(username='profesor1').exists():
                profesor = User.objects.create_user(
                    username='profesor1',
                    email='profesor@liceohualqui.cl',
                    password='profesor123',
                    first_name='Juan',
                    last_name='Pérez'
                )
                profesor.groups.add(profesor_group)
                self.stdout.write(self.style.SUCCESS("✅ Usuario profesor1 creado"))
            
            if not User.objects.filter(username='alumno1').exists():
                alumno = User.objects.create_user(
                    username='alumno1',
                    email='alumno@liceohualqui.cl',
                    password='alumno123',
                    first_name='María',
                    last_name='González'
                )
                alumno.groups.add(alumno_group)
                self.stdout.write(self.style.SUCCESS("✅ Usuario alumno1 creado"))
            
            self.stdout.write(self.style.SUCCESS("✅ Datos de ejemplo creados"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creando datos de ejemplo: {e}"))
