import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/mis_asistencias.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Broad regex pattern to catch the split tag with any whitespace characters (newlines, spaces, tabs)
    # Target: {{ asistencia.registrado_por.get_full_name|default:asistencia.registrado_por.username }}
    # It might be split like {{ \n value \n }} or {{value\n}} etc.
    
    # We look for the start and end of the tag and the key content "registrado_por.username"
    pattern = r'\{\{\s*asistencia\.registrado_por\.get_full_name\|default:asistencia\.registrado_por\.username\s*\}\}'
    
    # Also try a more generic one if the above is too specific on whitespace
    # Matches {{ (anything) asistencia.registrado_por.username (anything) }} across lines
    pattern_generic = r'\{\{[^}]*asistencia\.registrado_por\.username[^}]*\}\}'
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
         print("Specific pattern not found. Trying generic pattern...")
         match = re.search(pattern_generic, content, re.DOTALL)
    
    if match:
        print(f"Found match: {match.group(0)!r}")
        # Replacement: Single line, clean
        replacement = '{{ asistencia.registrado_por.get_full_name|default:asistencia.registrado_por.username }}'
        
        # We use strict replacement on the specific match to avoid accidents
        new_content = content.replace(match.group(0), replacement)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found matching patterns.")
        # Debug dump of lines around where it should be
        if "registrado_por" in content:
            print("Context dump:")
            idx = content.find("registrado_por")
            print(repr(content[idx-50:idx+100]))

except Exception as e:
    print(f"Error: {e}")
