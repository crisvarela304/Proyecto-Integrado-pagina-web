import os
import sys
import django

# Setup Django
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def fix_permissions():
    print("Fixing user permissions...")
    
    # Find users who are staff but NOT superusers
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    
    count = 0
    for user in staff_users:
        print(f"Revoking staff status for: {user.username} ({user.email})")
        user.is_staff = False
        user.save()
        count += 1
        
    print(f"\nDone. Revoked staff status from {count} users.")
    print("Only superusers now have access to the Django Admin panel.")

if __name__ == "__main__":
    fix_permissions()
