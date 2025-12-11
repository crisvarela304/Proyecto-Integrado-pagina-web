from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Curso
from core.models import ConfiguracionAcademica
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import openpyxl

class ImportacionUsuariosTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.curso = Curso.objects.create(nombre='1 Medio A', nivel='1_medio', activo=True)
        ConfiguracionAcademica.objects.update_or_create(pk=1, defaults={'año_actual': 2024})

    def test_import_excel_valid(self):
        self.client.force_login(self.admin_user)
        
        # Crear Excel en memoria
        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['RUT', 'Nombres', 'Apellidos', 'Email'])
        ws.append(['11111111-1', 'Juan', 'Perez', 'juan@test.com'])
        wb.save(output)
        output.seek(0)
        
        excel_file = SimpleUploadedFile(
            "test_import.xlsx",
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        url = reverse('admin:usuarios_perfilusuario_import_csv')
        data = {
            'curso': self.curso.id,
            'archivo': excel_file
        }
        
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verificar creación
        self.assertTrue(User.objects.filter(username='11111111-1').exists())
        user = User.objects.get(username='11111111-1')
        self.assertEqual(user.first_name, 'Juan')
        self.assertTrue(user.perfil.tipo_usuario, 'estudiante')
