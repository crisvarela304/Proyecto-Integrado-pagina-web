import os
import sys
import django
import random
from itertools import cycle

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Curso, InscripcionCurso

def digito_verificador(rut):
    reversed_digits = map(int, reversed(str(rut)))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(reversed_digits, factors))
    mod = (-s) % 11
    if mod == 10: return 'K'
    if mod == 11: return '0'
    return str(mod)

def generar_rut():
    numero = random.randint(22000000, 25000000)
    dv = digito_verificador(numero)
    return f"{numero}-{dv}"

def populate_students():
    print("Iniciando generación de estudiantes de prueba...")
    
    nombres_hombres = [
        "Juan", "Pedro", "Luis", "Diego", "Carlos", "José", "Miguel", "Francisco", 
        "David", "Jorge", "Matías", "Nicolás", "Benjamín", "Joaquín", "Lucas", 
        "Vicente", "Agustín", "Martín", "Tomás", "Gabriel"
    ]
    
    nombres_mujeres = [
        "María", "Ana", "Carmen", "Sofía", "Valentina", "Camila", "Isabella", 
        "Javiera", "Constanza", "Martina", "Catalina", "Fernanda", "Antonia", 
        "Florencia", "Isidora", "Emilia", "Francisca", "Josefa", "Amanda", "Victoria"
    ]
    
    apellidos = [
        "González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva",
        "Martínez", "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández",
        "Torres", "Araya", "Flores", "Espinoza", "Valenzuela", "Castillo", "Tapia",
        "Reyes", "Gutiérrez", "Castro", "Pizarro", "Álvarez", "Vásquez", "Sánchez", "Fernández"
    ]
    
    cursos = list(Curso.objects.filter(activo=True))
    if not cursos:
        print("¡Error! No hay cursos activos. Crea cursos primero.")
        return

    count = 0
    target_students = 20
    
    for _ in range(target_students):
        # Generar datos
        es_hombre = random.choice([True, False])
        nombre = random.choice(nombres_hombres if es_hombre else nombres_mujeres)
        apellido_paterno = random.choice(apellidos)
        apellido_materno = random.choice(apellidos)
        
        rut = generar_rut()
        while PerfilUsuario.objects.filter(rut=rut).exists():
            rut = generar_rut()
            
        username = rut  # El username será el RUT
        password = rut.split('-')[0]  # La contraseña serán los primeros números del RUT
        email = f"{nombre.lower()}.{apellido_paterno.lower()}@liceo.cl"
        
        # Crear Usuario
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=f"{apellido_paterno} {apellido_materno}"
            )
            
            # Crear Perfil
            PerfilUsuario.objects.create(
                user=user,
                rut=rut,
                tipo_usuario='estudiante',
                direccion=f"Calle Falsa {random.randint(100, 999)}, Hualqui",
                telefono=f"+569{random.randint(10000000, 99999999)}"
            )
            
            # Inscribir en curso aleatorio
            curso = random.choice(cursos)
            InscripcionCurso.objects.create(
                estudiante=user,
                curso=curso,
                año=2024
            )
            
            # Actualizar contador de alumnos en el curso
            curso.total_alumnos = InscripcionCurso.objects.filter(curso=curso, estado='activo').count()
            curso.save()
            
            print(f"Creado: {nombre} {apellido_paterno} ({rut}) - Curso: {curso}")
            count += 1
            
    print(f"\n¡Listo! Se han creado {count} estudiantes nuevos.")
    print("Las credenciales son:")
    print("Usuario: [RUT completo, ej: 12345678-9]")
    print("Contraseña: [Números del RUT, ej: 12345678]")

if __name__ == '__main__':
    populate_students()
