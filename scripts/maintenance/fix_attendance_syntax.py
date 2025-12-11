import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/mis_asistencias.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of "=='" with " == '" inside {% if %} tags
# The error pattern is specifically "estado_seleccionado=='presente'" etc.
# We can just replace "=='" with " == '" globally or within the select block context

# Safer: specific replacement for the known bad lines
new_content = content.replace("estado_seleccionado=='presente'", "estado_seleccionado == 'presente'")
new_content = new_content.replace("estado_seleccionado=='ausente'", "estado_seleccionado == 'ausente'")
new_content = new_content.replace("estado_seleccionado=='tardanza'", "estado_seleccionado == 'tardanza'")
new_content = new_content.replace("estado_seleccionado=='justificado'", "estado_seleccionado == 'justificado'")

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed syntax errors in {file_path}")
else:
    print("No changes needed (or pattern not found).")
