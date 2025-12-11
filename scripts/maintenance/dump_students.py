import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import InscripcionCurso

with open('students_list.txt', 'w', encoding='utf-8') as f:
    f.write(f"{'RUT':<15} | {'NOMBRE COMPLETO':<40} | {'CURSO(S)':<20}\n")
    f.write("-" * 80 + "\n")

    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante').order_by('last_name')

    for est in estudiantes:
        rut = est.perfil.rut if hasattr(est, 'perfil') else 'S/RUT'
        nombre = est.get_full_name()
        
        inscripciones = InscripcionCurso.objects.filter(estudiante=est, estado='activo')
        cursos = ", ".join([str(i.curso) for i in inscripciones]) if inscripciones.exists() else "Sin curso"
        
        f.write(f"{rut:<15} | {nombre:<40} | {cursos:<20}\n")
    
    print("Listado generado en students_list.txt")
