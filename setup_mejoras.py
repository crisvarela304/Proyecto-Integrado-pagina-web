#!/usr/bin/env python
"""
Script para aplicar las migraciones y configurar el sistema
Plataforma Institucional del Liceo Juan Bautista de Hualqui
Versión: 2.0 - Intranet Profesional
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y muestra su progreso"""
    print(f"\n🔄 {description}...")
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completado exitosamente")
        if result.stdout:
            print(f"Salida: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("=" * 80)
    print("🚀 CONFIGURACIÓN DE MEJORAS - LICEO JUAN BAUTISTA DE HUALQUI")
    print("=" * 80)
    print("Versión: 2.0 - Intranet Profesional")
    print("Fecha: 06-11-2025")
    print()
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: No se encontró manage.py")
        print("   Asegúrate de ejecutar este script desde el directorio del proyecto Django")
        return False
    
    # Paso 1: Crear migraciones
    print("\n📋 PASO 1: CREAR MIGRACIONES")
    print("=" * 50)
    
    apps = ['comunicacion', 'usuarios']
    success = True
    
    for app in apps:
        if not run_command(f'python manage.py makemigrations {app}', 
                          f'Crear migraciones para {app}'):
            success = False
    
    if not success:
        print("❌ Error al crear migraciones")
        return False
    
    # Paso 2: Aplicar migraciones
    print("\n📋 PASO 2: APLICAR MIGRACIONES A LA BASE DE DATOS")
    print("=" * 50)
    
    if not run_command('python manage.py migrate', 'Aplicar migraciones'):
        print("❌ Error al aplicar migraciones")
        return False
    
    # Paso 3: Recopilar archivos estáticos
    print("\n📋 PASO 3: RECOPILAR ARCHIVOS ESTÁTICOS")
    print("=" * 50)
    
    if not run_command('python manage.py collectstatic --noinput', 
                      'Recopilar archivos estáticos'):
        print("⚠️  Advertencia: No se pudieron recopilar los archivos estáticos")
    
    # Paso 4: Crear superusuario (opcional)
    print("\n📋 PASO 4: CONFIGURACIÓN DE ADMINISTRADOR")
    print("=" * 50)
    
    create_superuser = input("\n¿Deseas crear un superusuario ahora? (s/n): ").lower().strip()
    if create_superuser in ['s', 'si', 'sí', 'y', 'yes']:
        if not run_command('python manage.py createsuperuser', 
                          'Crear superusuario'):
            print("⚠️  No se pudo crear el superusuario automáticamente")
            print("   Puedes crearlo después ejecutando: python manage.py createsuperuser")
    
    # Paso 5: Verificar configuración
    print("\n📋 PASO 5: VERIFICACIÓN FINAL")
    print("=" * 50)
    
    # Verificar que los archivos existen
    files_to_check = [
        'usuarios/models.py',
        'comunicacion/models.py', 
        'usuarios/views.py',
        'comunicacion/views.py',
        'usuarios/templates/usuarios/login.html',
        'comunicacion/templates/comunicacion/noticias_list.html'
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            all_files_exist = False
    
    if all_files_exist:
        print("\n✅ Todos los archivos de mejoras están presentes")
    else:
        print("\n⚠️  Algunos archivos no se encontraron. Verifica la instalación.")
    
    # Instrucciones finales
    print("\n" + "=" * 80)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print()
    print("1. 🔑 ACCESO AL ADMIN:")
    print("   - URL: http://localhost:8000/admin/")
    print("   - Usuario: (el que creaste como superusuario)")
    print()
    print("2. 📰 GESTIÓN DE NOTICIAS:")
    print("   - Ve a la sección 'Comunicaciones' en el admin")
    print("   - Crea categorías de noticias")
    print("   - Publica noticias de ejemplo")
    print()
    print("3. 👥 GESTIÓN DE USUARIOS:")
    print("   - Ve a la sección 'Usuarios' en el admin")
    print("   - Crea perfiles de usuario con RUTs válidos")
    print()
    print("4. 🌐 ACCESO AL SITIO:")
    print("   - Público: http://localhost:8000/")
    print("   - Login: http://localhost:8000/usuarios/login/")
    print("   - Panel: http://localhost:8000/usuarios/panel/")
    print()
    print("5. 📊 FUNCIONALIDADES DISPONIBLES:")
    print("   ✅ Búsqueda y filtrado de noticias")
    print("   ✅ Categorización de contenido")
    print("   ✅ Autenticación por RUT chileno")
    print("   ✅ Panel de usuario personalizado")
    print("   ✅ Sistema de permisos por tipo de usuario")
    print("   ✅ Validación de formularios en tiempo real")
    print("   ✅ Interfaz responsive y moderna")
    print()
    print("6. 🔧 SOLUCIÓN DE PROBLEMAS:")
    print("   - Si hay errores, revisa los logs de Django")
    print("   - Verifica que SQLite3 esté disponible")
    print("   - Asegúrate de tener todas las dependencias instaladas")
    print()
    print("📞 SOPORTE:")
    print("   - Documentación: RESUMEN_MEJORAS_IMPLEMENTADAS.md")
    print("   - Código de ejemplo incluido en los templates")
    print()
    print("=" * 80)
    print("🎓 ¡LICEO JUAN BAUTISTA DE HUALQUI - PLATAFORMA ACTUALIZADA! 🎓")
    print("=" * 80)
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        print("\n❌ La configuración no se completó correctamente")
        sys.exit(1)
    else:
        print("\n🎉 ¡Configuración completada exitosamente!")
        sys.exit(0)
