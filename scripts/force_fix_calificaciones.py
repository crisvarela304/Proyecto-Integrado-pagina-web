import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/mis_calificaciones.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: {{ [whitespace] calificacion.get_tipo_evaluacion_display [whitespace] }}
    pattern = r'\{\{\s*calificacion\.get_tipo_evaluacion_display\s*\}\}'
    
    # Replacement: Single line
    replacement = '{{ calificacion.get_tipo_evaluacion_display }}'
    
    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        print(f"Found {count} broken tags. Fixing...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found (or regex didn't match). Checking context...")
        if "get_tipo_evaluacion_display" in content:
            idx = content.find("get_tipo_evaluacion_display")
            print(f"Context: {repr(content[idx-20:idx+50])}")

except Exception as e:
    print(f"Error: {e}")
