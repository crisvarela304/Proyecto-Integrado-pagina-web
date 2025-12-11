import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from usuarios.models import PerfilUsuario

def list_ruts():
    perfiles = PerfilUsuario.objects.all().order_by('user__last_name', 'user__first_name')
    count = perfiles.count()
    
    output_path = os.path.join(os.path.dirname(__file__), 'ruts_list.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Total de usuarios encontrados: {count}\n\n")
        f.write(f"{'NOMBRE COMPLETO':<40} | {'USUARIO':<15} | {'RUT':<15} | {'TIPO'}\n")
        f.write("-" * 90 + "\n")
        
        for perfil in perfiles:
            nombre = perfil.user.get_full_name() or "Sin nombre"
            usuario = perfil.user.username
            rut = perfil.rut or "Sin RUT"
            tipo = perfil.get_tipo_usuario_display()
            
            f.write(f"{nombre:<40} | {usuario:<15} | {rut:<15} | {tipo}\n")
            
    print(f"Listado guardado en {output_path}")

if __name__ == '__main__':
    list_ruts()
