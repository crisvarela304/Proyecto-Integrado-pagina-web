
import os

path = r"C:\Users\crist\AppData\Local\Programs\Python\Python313\Lib\site-packages\jazzmin\templates\admin\includes\fieldset.html"

try:
    with open(path, 'r', encoding='utf-8') as f:
        with open('jazzmin_fieldset_dump.html', 'w', encoding='utf-8') as out:
            out.write(f.read())
except Exception as e:
    print(f"Error reading file: {e}")
