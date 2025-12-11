import os

# Define path relative to project root
path = r"apps\comunicacion\templates\comunicacion\noticias_list.html"
base_dir = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web"
full_path = os.path.join(base_dir, path)

print(f"Reading {full_path}...")
try:
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The specific bad string from traceback
    bad_string = "{% if categoria_filtro==cat.nombre %}"
    good_string = "{% if categoria_filtro == cat.nombre %}"

    if bad_string in content:
        print("Found bad syntax. Fixing...")
        new_content = content.replace(bad_string, good_string)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Fixed and Saved.")
    else:
        print("Target string NOT found. Checking via loose regex/check...")
        # Check if maybe indentation is weird or spaces are partial
        if "categoria_filtro==cat.nombre" in content:
             print("Found loose match 'categoria_filtro==cat.nombre'. Replacing...")
             new_content = content.replace("categoria_filtro==cat.nombre", "categoria_filtro == cat.nombre")
             with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
             print("Fixed loose match and Saved.")
        else:
            print("No errors found. File might be already clean or content different.")
            
            # Print the line to be sure
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "categoria_filtro" in line:
                    print(f"Line {i+1}: {line.strip()}")

except Exception as e:
    print(f"Error: {e}")
