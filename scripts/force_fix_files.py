import os

files_to_fix = [
    {
        "path": r"apps\academico\templates\academico\curso_inscripciones.html",
        "search": """{{ inscripcion.estudiante.first_name|first }}{{
                                        inscripcion.estudiante.last_name|first }}""",
        "replace": """{{ inscripcion.estudiante.first_name|first }}{{ inscripcion.estudiante.last_name|first }}"""
    },
    {
        "path": r"apps\documentos\templates\documentos\documentos_list.html",
        "search": """<i class="bi bi-person"></i> {{
                                documento.creado_por.get_full_name|default:documento.creado_por.username }}""",
        "replace": """<i class="bi bi-person"></i> {{ documento.creado_por.get_full_name|default:documento.creado_por.username }}"""
    }
]

base_dir = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web"

for item in files_to_fix:
    full_path = os.path.join(base_dir, item["path"])
    print(f"Checking {item['path']}...")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Normalize indentation for search (flexible check)
        # Actually better to just use regex sub or replace known exact blocks if possible
        # Let's try exact replace first since I copied from view_file
        
        if item["search"] in content:
            print("  Found bad block. Fixing...")
            new_content = content.replace(item["search"], item["replace"])
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("  Fixed and Saved.")
        else:
            print("  Block NOT found (maybe mismatch in indentation).")
            # Try a looser replace just in case (regex)
            import re
            # specific to curso_inscripciones
            if "curso_inscripciones" in item["path"]:
                pattern = re.compile(r'\{\{\s*inscripcion\.estudiante\.first_name\|first\s*\}\}\{\{\s*[\r\n]+\s*inscripcion\.estudiante\.last_name\|first\s*\}\}')
                if pattern.search(content):
                    print("  Found via Regex. Fixing...")
                    new_content = pattern.sub('{{ inscripcion.estudiante.first_name|first }}{{ inscripcion.estudiante.last_name|first }}', content)
                    with open(full_path, 'w', encoding='utf-8') as f:
                         f.write(new_content)
                    print("  Fixed via Regex.")

            # specific to documentos
            if "documentos_list" in item["path"]:
                pattern = re.compile(r'bi-person"></i>\s*\{\{\s*[\r\n]+\s*documento\.creado_por')
                if pattern.search(content):
                     print("  Found via Regex (documentos). Fixing...")
                     # Use a simpler replace for this one
                     new_content = re.sub(r'bi-person"></i>\s*\{\{\s*[\r\n]+\s*', 'bi-person"></i> {{ ', content)
                     with open(full_path, 'w', encoding='utf-8') as f:
                         f.write(new_content)
                     print("  Fixed via Regex (documentos).")

    except Exception as e:
        print(f"  Error: {e}")
