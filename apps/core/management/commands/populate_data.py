from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from usuarios.models import PerfilUsuario
from academico.models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia
from comunicacion.models import Noticia
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos iniciales y usuarios reales para pruebas'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Iniciando configuración de datos base"))
        self.stdout.write(self.style.SUCCESS("Liceo Juan Bautista de Hualqui - Intranet"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        try:
            self.limpiar_datos()
            self.crear_grupos()
            self.crear_usuarios()
            self.crear_asignaturas()
            self.crear_noticias()

            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write("\n📊 RESUMEN:")
            self.stdout.write(f"   • Usuarios Totales: {User.objects.count()}")
            self.stdout.write(f"   • Perfiles: {PerfilUsuario.objects.count()}")
            self.stdout.write(f"   • Asignaturas: {Asignatura.objects.count()}")
            self.stdout.write(f"   • Noticias: {Noticia.objects.count()}")
            
            self.stdout.write("\n🔐 CREDENCIALES DE ACCESO:")
            self.stdout.write("   1. ADMINISTRADOR:")
            self.stdout.write("      User: admin")
            self.stdout.write("      Pass: admin123")
            
            self.stdout.write("\n   2. PROFESORES (2):")
            self.stdout.write("      User: prof.roberto  | Pass: profesor123")
            self.stdout.write("      User: prof.laura    | Pass: profesor123")
            
            self.stdout.write("\n   3. ESTUDIANTES (3):")
            self.stdout.write("      User: est.lucas     | Pass: estudiante123")
            self.stdout.write("      User: est.martina   | Pass: estudiante123")
            self.stdout.write("      User: est.sofia     | Pass: estudiante123")
            
            self.stdout.write("\n⚠️ NOTA: Los estudiantes NO tienen cursos asignados.")
            self.stdout.write("   Debe ingresar como ADMIN para crear cursos y asignar alumnos/profesores.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante la configuración: {str(e)}"))
            import traceback
            traceback.print_exc()

    def limpiar_datos(self):
        self.stdout.write("Limpiando datos antiguos...")
        
        # Eliminar todos los usuarios excepto admin
        # Primero eliminamos perfiles para evitar problemas de integridad
        PerfilUsuario.objects.exclude(user__username='admin').delete()
        User.objects.exclude(username='admin').delete()
        
        # Eliminar datos académicos dependientes
        Curso.objects.all().delete()
        Asignatura.objects.all().delete()
        Noticia.objects.all().delete()
        
        self.stdout.write("Datos antiguos eliminados.")

    def crear_grupos(self):
        self.stdout.write("Configurando grupos y permisos...")
        
        grupos = ['Profesores', 'Estudiantes', 'Administrativos']
        for nombre in grupos:
            grupo, created = Group.objects.get_or_create(name=nombre)
            
            if nombre == 'Profesores':
                # Asignar permisos a Profesores
                permisos_codenames = [
                    # Asistencia
                    'add_asistencia', 'change_asistencia', 'view_asistencia',
                    # Calificaciones
                    'add_calificacion', 'change_calificacion', 'view_calificacion',
                    # Lectura general
                    'view_curso', 'view_asignatura', 'view_inscripcioncurso',
                    'view_user', 'view_perfilusuario'
                ]
                
                for codename in permisos_codenames:
                    try:
                        perm = Permission.objects.get(codename=codename)
                        grupo.permissions.add(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Permiso no encontrado: {codename}"))

    def crear_usuarios(self):
        self.stdout.write("Creando usuarios...")
        self.stdout.write(f"RUTs existentes: {list(PerfilUsuario.objects.values_list('rut', flat=True))}")
        conflicting_user = PerfilUsuario.objects.filter(rut='12345678-9').first()
        if conflicting_user:
            self.stdout.write(f"Dueño del RUT 12345678-9: {conflicting_user.user.username}")
        
        # 1. Usuario Administrador (si no existe)
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@liceohualqui.cl',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                is_staff=True,
                is_superuser=True
            )
            PerfilUsuario.objects.create(
                user=admin,
                rut='11111111-1',
                tipo_usuario='administrativo',
                telefono='+56 9 1111 1111'
            )
        else:
            # Asegurar que el admin tenga el RUT correcto para liberar otros RUTs
            admin = User.objects.get(username='admin')
            if hasattr(admin, 'perfil'):
                admin.perfil.rut = '11111111-1'
                admin.perfil.save()
            else:
                PerfilUsuario.objects.create(
                    user=admin,
                    rut='11111111-1',
                    tipo_usuario='administrativo',
                    telefono='+56 9 1111 1111'
                )
        
        # 2. Profesores Reales (2)
        profesores = [
            {
                'username': 'prof.roberto',
                'first': 'Roberto', 'last': 'Carlos',
                'rut': '12345678-9', 'email': 'roberto.carlos@liceohualqui.cl'
            },
            {
                'username': 'prof.laura',
                'first': 'Laura', 'last': 'Pausini',
                'rut': '98765432-1', 'email': 'laura.pausini@liceohualqui.cl'
            }
        ]

        grupo_profesores = Group.objects.get(name='Profesores')

        for data in profesores:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='profesor123',
                    first_name=data['first'],
                    last_name=data['last']
                )
                PerfilUsuario.objects.create(
                    user=user,
                    rut=data['rut'],
                    tipo_usuario='profesor',
                    telefono='+56 9 9876 5432'
                )
                user.groups.add(grupo_profesores)

        # 3. Estudiantes Reales (3)
        estudiantes = [
            {
                'username': 'est.lucas',
                'first': 'Lucas', 'last': 'Silva',
                'rut': '21123456-7', 'email': 'lucas.silva@liceohualqui.cl'
            },
            {
                'username': 'est.martina',
                'first': 'Martina', 'last': 'Rojas',
                'rut': '21123456-8', 'email': 'martina.rojas@liceohualqui.cl'
            },
            {
                'username': 'est.sofia',
                'first': 'Sofía', 'last': 'Vargas',
                'rut': '21123456-9', 'email': 'sofia.vargas@liceohualqui.cl'
            }
        ]

        grupo_estudiantes = Group.objects.get(name='Estudiantes')

        for data in estudiantes:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='estudiante123',
                    first_name=data['first'],
                    last_name=data['last']
                )
                PerfilUsuario.objects.create(
                    user=user,
                    rut=data['rut'],
                    tipo_usuario='estudiante',
                    telefono='+56 9 1234 5678'
                )
                user.groups.add(grupo_estudiantes)

    def crear_asignaturas(self):
        self.stdout.write("Creando asignaturas base...")
        
        asignaturas_data = [
            ('MAT101', 'Matemáticas', 4),
            ('LEN101', 'Lenguaje y Comunicación', 4),
            ('HIS101', 'Historia y Geografía', 3),
            ('CIE101', 'Ciencias Naturales', 3),
            ('ING101', 'Inglés', 3),
            ('ART101', 'Artes Visuales', 2),
            ('MUS101', 'Música', 2),
            ('EDU101', 'Educación Física', 2),
        ]
        
        for codigo, nombre, horas in asignaturas_data:
            Asignatura.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'horas_semanales': horas,
                    'activa': True
                }
            )

    def crear_noticias(self):
        self.stdout.write("Creando noticias de ejemplo...")
        
        admin = User.objects.filter(username='admin').first()
        if not admin: return

        noticias = [
            {
                'titulo': 'Inicio del Año Escolar 2024',
                'bajada': 'Bienvenidos a un nuevo ciclo académico en nuestro liceo.',
                'cuerpo': 'Estimada comunidad, damos la bienvenida a este nuevo año escolar...',
                'categoria': 'administrativo',
                'destacado': True
            },
            {
                'titulo': 'Horario de Atención Apoderados',
                'bajada': 'Conoce los nuevos horarios de atención para este semestre.',
                'cuerpo': 'La atención de apoderados se realizará los días...',
                'categoria': 'comunicado',
                'destacado': False
            }
        ]
        
        for n in noticias:
            Noticia.objects.get_or_create(
                titulo=n['titulo'],
                defaults={
                    'bajada': n['bajada'],
                    'cuerpo': n['cuerpo'],
                    'categoria': n['categoria'],
                    'destacado': n['destacado'],
                    'autor': admin,
                    'es_publica': True
                }
            )
