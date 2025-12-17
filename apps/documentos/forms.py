from django import forms
from django.utils import timezone
import os

from .models import Documento


class DocumentoForm(forms.ModelForm):
    """Formulario sencillo para subir documentos al portal."""

    class Meta:
        model = Documento
        fields = [
            'titulo',
            'descripcion',
            'archivo',
            'categoria',
            'tipo',
            'visibilidad',
            'tags',
            'version',
            'es_oficial',
            'publicado',
            'fecha_publicacion',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.TextInput(attrs={'placeholder': 'separa por comas'}),
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        if not self.initial.get('fecha_publicacion'):
            self.initial['fecha_publicacion'] = timezone.now().date()
        
        # Filtrado de categorías según rol
        if self.usuario:
            from django.db.models import Q
            from .models import CategoriaDocumento
            
            perfil = getattr(self.usuario, 'perfil', None)
            es_profesor = perfil and perfil.tipo_usuario == 'profesor'
            es_admin = self.usuario.is_staff or (perfil and perfil.tipo_usuario in ['administrativo', 'directivo'])
            
            if es_profesor and not es_admin:
                # Profesores BLOQUEADOS a solo Material de Estudio
                self.fields['categoria'].queryset = CategoriaDocumento.objects.filter(
                    Q(nombre__icontains='estudio') | 
                    Q(nombre__icontains='guía') | 
                    Q(nombre__icontains='asignatura') | 
                    Q(nombre__icontains='material')
                )
                # El curso lo debo filtrar también para que solo vea SUS cursos
                from academico.models import Curso
                self.fields['curso'].queryset = Curso.objects.filter(
                    Q(profesor_jefe=self.usuario) | Q(horario__profesor=self.usuario)
                ).distinct()
                self.fields['curso'].required = True # Exigir curso para ordenar el material
                
                # Visibilidad: Restringir a publico o solo estudiantes
                self.fields['visibilidad'].choices = [
                    ('publico', 'Público'),
                    ('solo_estudiantes', 'Solo Estudiantes'),
                ]
                
            elif es_admin:
                # Administrativos: Solo Certificados y documentos oficiales
                self.fields['categoria'].queryset = CategoriaDocumento.objects.filter(
                    Q(nombre__icontains='certificado') | 
                    Q(nombre__icontains='acta') | 
                    Q(nombre__icontains='resolución') | 
                    Q(nombre__icontains='circular') |
                    Q(nombre__icontains='administrativo') |
                    Q(nombre__icontains='institucional') |
                    Q(nombre__icontains='reglamento')
                )
                # Admins pueden ver todos los cursos o ninguno (global)
                # No restringimos curso, pero lo hacemos opcional
                self.fields['curso'].required = False

    EXTENSIONES_PERMITIDAS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                               '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.txt']
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise forms.ValidationError("Debes adjuntar un archivo.")
        if archivo.size == 0:
            raise forms.ValidationError("El archivo está vacío.")
        
        # Validar tamaño máximo
        if archivo.size > self.MAX_UPLOAD_SIZE:
            raise forms.ValidationError(f"El archivo excede el tamaño máximo permitido de 10MB.")
        
        # Validar extensión
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in self.EXTENSIONES_PERMITIDAS:
            raise forms.ValidationError(
                f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(self.EXTENSIONES_PERMITIDAS)}"
            )
        
        return archivo

    def save(self, commit=True):
        documento = super().save(commit=False)
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            setattr(documento, 'tamaño', archivo.size)
            inferred = self._infer_tipo_desde_nombre(archivo.name)
            if inferred:
                documento.tipo = inferred
        if self.usuario:
            documento.creado_por = self.usuario
        if commit:
            documento.save()
            self.save_m2m()
        return documento

    @staticmethod
    def _infer_tipo_desde_nombre(nombre_archivo: str) -> str:
        ext = os.path.splitext(nombre_archivo)[1].lower()
        mapping = {
            '.pdf': 'pdf',
            '.doc': 'doc',
            '.docx': 'doc',
            '.xls': 'xls',
            '.xlsx': 'xls',
            '.ppt': 'ppt',
            '.pptx': 'ppt',
            '.jpg': 'img',
            '.jpeg': 'img',
            '.png': 'img',
            '.zip': 'zip',
            '.rar': 'zip',
        }
        return mapping.get(ext)
