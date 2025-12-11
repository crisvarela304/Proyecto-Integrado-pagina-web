import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academico.models import Calificacion, Curso, Asignatura
from django.contrib.auth.models import User

try:
    print("Querying Calificacion...")
    print(Calificacion.objects.all().count())
    print("Query success.")
except Exception as e:
    print(f"Error: {e}")
