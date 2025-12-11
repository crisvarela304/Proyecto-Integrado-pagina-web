import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def check_admin():
    admins = User.objects.filter(is_superuser=True)
    if admins.exists():
        print(f"Superusuarios encontrados: {admins.count()}")
        for admin in admins:
            print(f" - Username: {admin.username}, Email: {admin.email}")
            # Reset password to 'admin123' for convenience if it's 'admin'
            if admin.username == 'admin':
                admin.set_password('admin123')
                admin.save()
                print(f"   -> Password de 'admin' reseteada a 'admin123'")
    else:
        print("No se encontraron superusuarios.")
        # Create one
        User.objects.create_superuser('admin', 'admin@liceo.cl', 'admin123')
        print(" -> Superusuario 'admin' creado con password 'admin123'")

if __name__ == '__main__':
    check_admin()
