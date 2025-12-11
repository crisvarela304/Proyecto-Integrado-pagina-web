import re

path = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\academico\templates\academico\curso_inscripciones.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'\{\{[^}]*[\n\r]+[^}]*\}\}')
matches = pattern.findall(content)

print(f"Found {len(matches)} matches:")
for m in matches:
    print(f"MATCH: --->{m}<---")
