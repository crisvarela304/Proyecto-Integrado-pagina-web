import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def create_admin():
    username = 'admin'
    password = 'admin123'
    email = 'admin@liceo.cl'
    
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Usuario '{username}' actualizado. Password: '{password}'")
    except User.DoesNotExist:
        User.objects.create_superuser(username, email, password)
        print(f"Usuario '{username}' creado. Password: '{password}'")

if __name__ == '__main__':
    create_admin()
