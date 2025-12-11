import os
import sys
import django
from django.contrib.auth import get_user_model, authenticate

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def diagnose():
    print("Diagnóstico de Usuario 'profesor1':")
    try:
        user = User.objects.get(username='profesor1')
        print(f"1. Usuario existe: SÍ (ID: {user.id})")
        print(f"2. is_active: {user.is_active}")
        print(f"3. is_staff: {user.is_staff}")
        print(f"4. Password correcta ('profe123'): {user.check_password('profe123')}")
        
        if hasattr(user, 'perfil'):
            print(f"5. Perfil existe: SÍ")
            print(f"6. Perfil activo: {user.perfil.activo}")
            print(f"7. Tipo usuario: {user.perfil.tipo_usuario}")
            print(f"8. RUT Perfil: {user.perfil.rut}")
        else:
            print("5. Perfil existe: NO (Esto es un problema para login_profesor)")

    except User.DoesNotExist:
        print("1. Usuario existe: NO (El script reset_users.py no se corrió o falló)")

if __name__ == '__main__':
    diagnose()
