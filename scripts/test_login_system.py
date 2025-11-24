#!/usr/bin/env python
"""
Script de prueba para verificar el sistema de login y registro
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_registration():
    """Prueba el registro de usuario"""
    print("🧪 Probando registro de usuario...")
    
    client = Client()
    
    # Datos de prueba
    test_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    }
    
    # Registrar usuario
    response = client.post('/usuarios/registrar/', data=test_data, follow=True)
    
    if response.status_code == 200:
        print("✅ Registro exitoso")
        
        # Verificar que el usuario se creó
        if User.objects.filter(username='testuser').exists():
            print("✅ Usuario creado en la base de datos")
            
            # Intentar login
            login_response = client.post('/usuarios/login/', 
                                       data={'username': 'testuser', 'password': 'TestPass123!'}, 
                                       follow=True)
            
            if login_response.status_code == 200:
                print("✅ Login exitoso")
                return True
            else:
                print("❌ Error en login")
                return False
        else:
            print("❌ Usuario no se creó en la base de datos")
            return False
    else:
        print("❌ Error en registro")
        print(f"Status code: {response.status_code}")
        return False

def test_login_form():
    """Prueba que el formulario de login se carga"""
    print("🧪 Probando formulario de login...")
    
    client = Client()
    response = client.get('/usuarios/login/')
    
    if response.status_code == 200:
        print("✅ Formulario de login se carga correctamente")
        return True
    else:
        print("❌ Error cargando formulario de login")
        return False

def test_news_list():
    """Prueba que la lista de noticias se carga"""
    print("🧪 Probando lista de noticias...")
    
    client = Client()
    response = client.get('/noticias/')
    
    if response.status_code == 200:
        print("✅ Lista de noticias se carga correctamente")
        return True
    else:
        print("❌ Error cargando lista de noticias")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas del sistema...")
    print("=" * 50)
    
    # Limpiar usuarios de prueba anteriores
    User.objects.filter(username='testuser').delete()
    
    tests = [
        test_login_form,
        test_news_list,
        test_registration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print("-" * 30)
        except Exception as e:
            print(f"❌ Error ejecutando {test.__name__}: {str(e)}")
            print("-" * 30)
    
    print("=" * 50)
    print(f"📊 Resultados: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El sistema está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar los logs.")
    
    # Limpiar usuarios de prueba
    User.objects.filter(username='testuser').delete()
    print("🧹 Limpieza de datos de prueba completada")

if __name__ == '__main__':
    main()
