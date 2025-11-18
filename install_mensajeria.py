#!/usr/bin/env python3
"""
Script de instalación y configuración del Sistema de Mensajería Segura
Liceo Juan Bautista de Hualqui
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def check_dependencies():
    """Verifica dependencias necesarias"""
    print("🔍 Verificando dependencias...")
    
    # Verificar Django
    try:
        import django
        print(f"✅ Django {django.get_version()} detectado")
    except ImportError:
        print("❌ Django no encontrado. Instalar con: pip install django")
        return False
    
    # Verificar Pillow para manejo de imágenes
    try:
        import PIL
        print("✅ Pillow detectado")
    except ImportError:
        print("⚠️  Pillow no encontrado. Instalar con: pip install Pillow")
    
    return True

def install_mensajeria():
    """Configura la aplicación de mensajería"""
    print("🚀 Configurando Sistema de Mensajería...")
    
    # 1. Crear migraciones
    if not run_command("python manage.py makemigrations mensajeria", 
                      "Creando migraciones de mensajeria"):
        return False
    
    # 2. Ejecutar migraciones
    if not run_command("python manage.py migrate", 
                      "Ejecutando migraciones"):
        return False
    
    # 3. Recopilar archivos estáticos (si es necesario)
    if not run_command("python manage.py collectstatic --noinput", 
                      "Recopilando archivos estáticos"):
        return False
    
    print("✅ Sistema de Mensajería configurado correctamente")
    return True

def create_superuser():
    """Crea un superusuario para administración"""
    print("👤 Creando superusuario de administración...")
    
    try:
        # Intentar crear superusuario interactivamente
        result = subprocess.run(
            "python manage.py createsuperuser", 
            shell=True, 
            input="admin\nadmin@liceohualqui.cl\npassword123\npassword123\n",
            text=True,
            check=True
        )
        print("✅ Superusuario creado correctamente")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  No se pudo crear superusuario automáticamente")
        print("   Crear manualmente con: python manage.py createsuperuser")
        return True

def update_urls():
    """Actualiza las URLs del proyecto"""
    print("🔗 Actualizando configuración de URLs...")
    
    urls_path = Path("config/urls.py")
    if urls_path.exists():
        # Leer el archivo actual
        with open(urls_path, 'r') as f:
            content = f.read()
        
        # Verificar si ya está incluida
        if 'mensajeria.urls' not in content:
            # Agregar la inclusión
            if 'include(' not in content:
                content = content.replace(
                    'from django.contrib import admin',
                    'from django.contrib import admin\nfrom django.urls import path, include'
                )
            
            content = content.replace(
                "path('admin/', admin.site.urls),",
                """path('admin/', admin.site.urls),
    path('mensajeria/', include('mensajeria.urls', namespace='mensajeria')),"""
            )
            
            # Escribir el archivo actualizado
            with open(urls_path, 'w') as f:
                f.write(content)
            
            print("✅ URLs actualizadas correctamente")
        else:
            print("✅ URLs ya configuradas")
    else:
        print("❌ No se encontró config/urls.py")
        return False
    
    return True

def create_sample_data():
    """Crea datos de ejemplo para testing"""
    print("📊 Creando datos de ejemplo...")
    
    try:
        # Crear grupos si no existen
        from django.contrib.auth.models import Group
        from django.contrib.auth.models import User
        
        # Crear grupos
        alumno_group, created = Group.objects.get_or_create(name='Alumno')
        profesor_group, created = Group.objects.get_or_create(name='Profesor')
        
        # Crear usuarios de ejemplo
        if not User.objects.filter(username='profesor1').exists():
            profesor = User.objects.create_user(
                username='profesor1',
                email='profesor@liceohualqui.cl',
                password='profesor123',
                first_name='Juan',
                last_name='Pérez'
            )
            profesor.groups.add(profesor_group)
            print("✅ Usuario profesor1 creado")
        
        if not User.objects.filter(username='alumno1').exists():
            alumno = User.objects.create_user(
                username='alumno1',
                email='alumno@liceohualqui.cl',
                password='alumno123',
                first_name='María',
                last_name='González'
            )
            alumno.groups.add(alumno_group)
            print("✅ Usuario alumno1 creado")
        
        print("✅ Datos de ejemplo creados")
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de ejemplo: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("🎓 SISTEMA DE MENSAJERÍA SEGURA")
    print("=" * 50)
    print("Liceo Juan Bautista de Hualqui")
    print("Instalación y configuración automática")
    print("=" * 50)
    
    # Verificar directorio de trabajo
    if not Path("manage.py").exists():
        print("❌ Error: No se encontró manage.py")
        print("   Ejecutar este script desde el directorio raíz del proyecto Django")
        sys.exit(1)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Configurar sistema
    steps = [
        ("Configurando URLs", update_urls),
        ("Instalando Sistema de Mensajería", install_mensajeria),
        ("Creando superusuario", create_superuser),
        ("Creando datos de ejemplo", create_sample_data),
    ]
    
    for description, step_func in steps:
        print(f"\n🔄 {description}...")
        if not step_func():
            print(f"❌ Error en: {description}")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 INSTALACIÓN COMPLETADA")
    print("=" * 50)
    print("✅ Sistema de Mensajería Segura instalado correctamente")
    print("\n📋 PASOS SIGUIENTES:")
    print("1. Ejecutar: python manage.py runserver")
    print("2. Acceder a: http://127.0.0.1:8000/admin/")
    print("3. Iniciar sesión como superuser")
    print("4. Crear usuarios con los grupos 'Alumno' y 'Profesor'")
    print("5. Acceder a mensajería en: http://127.0.0.1:8000/mensajeria/")
    print("\n👥 USUARIOS DE PRUEBA:")
    print("   Profesor: profesor1 / profesor123")
    print("   Alumno: alumno1 / alumno123")
    print("\n🛡️  CARACTERÍSTICAS DE SEGURIDAD:")
    print("   • Protección XSS y CSRF")
    print("   • Rate Limiting")
    print("   • Validación de archivos")
    print("   • Control de acceso por roles")
    print("   • Panel de administración seguro")

if __name__ == "__main__":
    main()
