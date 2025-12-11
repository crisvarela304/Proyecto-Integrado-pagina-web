import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/mis_asistencias.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: {{ [whitespace] asistencia.registrado_por.get_full_name|default:asistencia.registrado_por.username [whitespace] }}
    # Using a flexible regex to capture split lines
    pattern = r'\{\{\s*asistencia\.registrado_por\.get_full_name\|default:asistencia\.registrado_por\.username\s*\}\}'
    
    # Replacement: Single line
    replacement = '{{ asistencia.registrado_por.get_full_name|default:asistencia.registrado_por.username }}'
    
    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        print(f"Found {count} broken tags. Fixing...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found (or regex didn't match). Checking for partial matches...")
        if "asistencia.registrado_por.username" in content:
             print("Partial match found. content verification:")
             start = content.find("asistencia.registrado_por.username") - 50
             end = content.find("asistencia.registrado_por.username") + 50
             print(repr(content[start:end]))

except Exception as e:
    print(f"Error: {e}")
