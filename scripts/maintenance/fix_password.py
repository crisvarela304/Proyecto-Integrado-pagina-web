import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def fix_passwords_and_create_users():
    print("Corrigiendo usuarios...")
    from usuarios.models import PerfilUsuario
    
    # 1. PROFESOR (Ya debería estar listo, pero aseguramos)
    target_rut_profe = '11111111-1'
    username_profe = 'profesor1'
    
    try:
        profesor = User.objects.get(username=username_profe)
        profesor.set_password('profe123')
        profesor.save()
        print(f"Password de '{username_profe}' verificada.")
    except User.DoesNotExist:
        print(f"Usuario '{username_profe}' no encontrado. Creando...")
        profesor = User.objects.create_user(username=username_profe, email='profesor1@liceo.cl', password='profe123')
        profesor.first_name = 'Juan'
        profesor.last_name = 'Pérez'
        profesor.save()

    # Asegurar perfil profesor
    perfil_profe, _ = PerfilUsuario.objects.get_or_create(user=profesor)
    if perfil_profe.rut != target_rut_profe:
        # Verificar conflicto antes de guardar
        if PerfilUsuario.objects.filter(rut=target_rut_profe).exclude(user=profesor).exists():
            PerfilUsuario.objects.filter(rut=target_rut_profe).exclude(user=profesor).delete()
        
        perfil_profe.rut = target_rut_profe
        perfil_profe.tipo_usuario = 'profesor'
        perfil_profe.save()
        print(f"Perfil de '{username_profe}' corregido.")

    # 2. ALUMNO
    target_rut_alumno = '22222222-2'
    username_alumno = 'alumno1'
    
    try:
        alumno = User.objects.get(username=username_alumno)
        alumno.set_password('alumno123')
        alumno.save()
        print(f"Password de '{username_alumno}' verificada.")
    except User.DoesNotExist:
        print(f"Usuario '{username_alumno}' no encontrado. Creando...")
        alumno = User.objects.create_user(username=username_alumno, email='alumno1@liceo.cl', password='alumno123')
        alumno.first_name = 'Pedro'
        alumno.last_name = 'González'
        alumno.save()
    
    # Asegurar perfil alumno
    perfil_alumno, _ = PerfilUsuario.objects.get_or_create(user=alumno)
    if perfil_alumno.rut != target_rut_alumno:
        # Verificar conflicto
        if PerfilUsuario.objects.filter(rut=target_rut_alumno).exclude(user=alumno).exists():
             PerfilUsuario.objects.filter(rut=target_rut_alumno).exclude(user=alumno).delete()

        perfil_alumno.rut = target_rut_alumno
        perfil_alumno.tipo_usuario = 'estudiante'
        perfil_alumno.save()
        print(f"Perfil de '{username_alumno}' corregido.")

if __name__ == '__main__':
    fix_passwords_and_create_users()
