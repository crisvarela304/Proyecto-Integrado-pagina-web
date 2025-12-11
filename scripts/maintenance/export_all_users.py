import os
import sys
import django
import csv

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def get_user_role(user):
    if user.is_superuser:
        return "Super Admin"
    
    # Try to get profile type
    try:
        if hasattr(user, 'perfil'):
            return user.perfil.get_tipo_usuario_display()
    except Exception:
        pass
        
    if user.is_staff:
        return "Staff / Admin"
        
    return "Usuario sin perfil"

def export_all_users():
    print("Exportando TODOS los usuarios...")
    
    users = User.objects.all().select_related('perfil').order_by('username')
    
    output_file = 'todos_los_usuarios.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ID', 'Username', 'Nombre Completo', 'Email', 'Rol / Tipo', 'Password (Hash)', 'Estado']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for user in users:
            writer.writerow({
                'ID': user.id,
                'Username': user.username,
                'Nombre Completo': user.get_full_name(),
                'Email': user.email,
                'Rol / Tipo': get_user_role(user),
                'Password (Hash)': user.password, # Full hash as requested
                'Estado': 'Activo' if user.is_active else 'Inactivo'
            })
            
    print(f"Exportación completada. Archivo: {output_file}")
    print(f"Total usuarios exportados: {users.count()}")

if __name__ == "__main__":
    export_all_users()
