import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/anotaciones/historial_anotaciones.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: {{ anotacion.get_categoria_display [whitespace] }}
    pattern = r'\{\{\s*anotacion\.get_categoria_display\s*\}\}'
    
    # Replacement: Single line
    replacement = '{{ anotacion.get_categoria_display }}'
    
    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        print(f"Found {count} broken tags. Fixing...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found (or regex didn't match).")
        # specific debug
        if "get_categoria_display" in content:
            print("Warning: 'get_categoria_display' exists in file.")
            idx = content.find("get_categoria_display")
            print(f"Context: {repr(content[idx-20:idx+50])}")

except Exception as e:
    print(f"Error: {e}")
