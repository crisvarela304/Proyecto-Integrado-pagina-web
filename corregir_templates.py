#!/usr/bin/env python
"""
Script para corregir automáticamente errores de sintaxis en templates Django
Corrige comparaciones sin espacios alrededor de ==
"""

import os
import re

# Directorio raíz del proyecto
BASE_DIR = r"C:\Users\crist\OneDrive\Escritorio\Proyecto integrado\Proyecto Integrado pagina web"

# Archivos a corregir
ARCHIVOS_A_CORREGIR = [
    r"academico\templates\academico\mis_calificaciones.html",
    r"documentos\templates\documentos\examenes_calendario.html",
    r"academico\templates\academico\profesor_mis_estudiantes.html",
    r"mensajeria\templates\mensajeria\simple_mensajeria.html",
]

def corregir_comparaciones(contenido):
    """
    Corrige comparaciones sin espacios alrededor de ==
    Ejemplo: {% if var==value %} -> {% if var == value %}
    """
    # Patrón para encontrar comparaciones sin espacios
    patron = r'(\{%\s+if\s+[^%]+)==([^%]+%\})'
    
    def reemplazar(match):
        return match.group(1) + ' == ' + match.group(2)
    
    # Aplicar corrección
    contenido_corregido = re.sub(patron, reemplazar, contenido)
    
    # También corregir elif
    patron_elif = r'(\{%\s+elif\s+[^%]+)==([^%]+%\})'
    contenido_corregido = re.sub(patron_elif, reemplazar, contenido_corregido)
    
    return contenido_corregido

def main():
    archivos_corregidos = 0
    
    for archivo_rel in ARCHIVOS_A_CORREGIR:
        archivo_path = os.path.join(BASE_DIR, archivo_rel)
        
        if not os.path.exists(archivo_path):
            print(f"❌ No encontrado: {archivo_rel}")
            continue
        
        try:
            # Leer archivo
            with open(archivo_path, 'r', encoding='utf-8') as f:
                contenido_original = f.read()
            
            # Corregir
            contenido_corregido = corregir_comparaciones(contenido_original)
            
            # Solo escribir si hubo cambios
            if contenido_original != contenido_corregido:
                with open(archivo_path, 'w', encoding='utf-8') as f:
                    f.write(contenido_corregido)
                print(f"✅ Corregido: {archivo_rel}")
                archivos_corregidos += 1
            else:
                print(f"ℹ️  Sin cambios: {archivo_rel}")
                
        except Exception as e:
            print(f"❌ Error en {archivo_rel}: {e}")
    
    print(f"\n✨ Total de archivos corregidos: {archivos_corregidos}")

if __name__ == "__main__":
    main()
