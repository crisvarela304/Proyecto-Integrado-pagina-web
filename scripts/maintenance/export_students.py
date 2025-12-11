import os
import sys
import django
import csv

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def export_students():
    print("Exportando estudiantes...")
    
    # Filtrar usuarios que son estudiantes
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    
    output_file = 'estudiantes_restantes.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Username', 'Nombre Completo', 'RUT', 'Email', 'Password (Hash)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for estudiante in estudiantes:
            writer.writerow({
                'Username': estudiante.username,
                'Nombre Completo': estudiante.get_full_name(),
                'RUT': estudiante.perfil.rut,
                'Email': estudiante.email,
                'Password (Hash)': estudiante.password[:20] + '...' # Solo mostramos hash parcial por seguridad
            })
            
    print(f"Exportación completada. Archivo: {output_file}")
    print(f"Total estudiantes: {estudiantes.count()}")

if __name__ == "__main__":
    export_students()
