import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def delete_user(username):
    try:
        user = User.objects.get(username=username)
        print(f"Found user: {user.username} (ID: {user.id})")
        
        # Profile check
        if hasattr(user, 'perfil'):
            print(f"User has profile: {user.perfil.tipo_usuario}")
            
        print("Deleting user and cascading relationships...")
        user.delete()
        print(f"User '{username}' deleted successfully.")
        
    except User.DoesNotExist:
        print(f"User '{username}' does not exist.")
    except Exception as e:
        print(f"Error deleting user: {e}")

if __name__ == "__main__":
    delete_user('estudiante1')
