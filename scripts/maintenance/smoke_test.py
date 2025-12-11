import os
import sys

# Setup Django FIRST
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from django.urls import reverse, resolve
from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser

def check_app_urls(app_name):
    print(f"\n🔍 ANALIZANDO APP: {app_name.upper()}")
    print("-" * 40)
    
    # Critical URLs to check per app
    url_names = []
    if app_name == 'core':
        url_names = ['home', 'contacto']
    elif app_name == 'usuarios':
        url_names = ['usuarios:login', 'usuarios:panel']
    elif app_name == 'academico':
        url_names = ['academico:dashboard_academico']
    elif app_name == 'administrativo':
        url_names = ['administrativo:dashboard']
    elif app_name == 'comunicacion':
        url_names = ['comunicacion:noticias']
    elif app_name == 'mensajeria':
        url_names = ['mensajeria:conversaciones_list']
        
    errors = 0
    for name in url_names:
        try:
            path = reverse(name)
            match = resolve(path)
            print(f"✅ URL '{name}' -> Resuelta correctamente: {match.func.__name__}")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO en URL '{name}': {e}")
            errors += 1
            
    if errors == 0:
        print(f"✨ App {app_name} parece estable en enrutamiento.")
    else:
        print(f"⚠️ App {app_name} tiene {errors} errores de URL.")

def check_view_execution():
    print(f"\n🧪 PRUEBA DE EJECUCIÓN DE VISTAS (Smoke Test)")
    print("-" * 40)
    factory = RequestFactory()
    
    # 1. Test Home (Public)
    try:
        from core.views import home
        request = factory.get('/')
        request.user = AnonymousUser()
        response = home(request)
        if response.status_code == 200:
            print("✅ Vista 'home' carga OK (200)")
        else:
            print(f"⚠️ Vista 'home' devolvió código {response.status_code}")
    except Exception as e:
        print(f"❌ Vista 'home' CRASH: {e}")

    # 2. Test Login Page
    try:
        from usuarios.views import login_usuario
        request = factory.get('/usuarios/login/')
        request.user = AnonymousUser()
        response = login_usuario(request)
        if response.status_code == 200:
            print("✅ Vista 'login' carga OK (200)")
        else:
            print(f"⚠️ Vista 'login' devolvió código {response.status_code}")
    except Exception as e:
        print(f"❌ Vista 'login' CRASH: {e}")

if __name__ == "__main__":
    apps_to_check = ['core', 'usuarios', 'academico', 'administrativo', 'comunicacion', 'mensajeria']
    
    # for app in apps_to_check:
    #     check_app_urls(app)
        
    check_view_execution()
