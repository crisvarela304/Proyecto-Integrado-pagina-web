import os
import sys
import django

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

def export_users_md():
    print("Generando reporte en Markdown...")
    
    users = User.objects.all().select_related('perfil').order_by('username')
    
    output_file = 'usuarios_credenciales.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Reporte de Usuarios y Credenciales\n\n")
        f.write("> [!NOTE]\n")
        f.write("> Las contraseñas se muestran como 'hashes' (encriptadas) por seguridad. Django no almacena las contraseñas reales.\n\n")
        
        f.write("| Usuario | Rol | Contraseña (Hash) | Estado |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        
        for user in users:
            role = get_user_role(user)
            status = "Activo" if user.is_active else "Inactivo"
            # Truncamos el hash para que la tabla no sea gigante, pero mostramos lo suficiente
            password_display = f"`{user.password[:20]}...`" 
            
            f.write(f"| {user.username} | **{role}** | {password_display} | {status} |\n")
            
    print(f"Reporte generado: {output_file}")
    print(f"Total usuarios: {users.count()}")

if __name__ == "__main__":
    export_users_md()
