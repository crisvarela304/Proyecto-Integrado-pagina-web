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

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise forms.ValidationError("Debes adjuntar un archivo.")
        if archivo.size == 0:
            raise forms.ValidationError("El archivo esta vacio.")
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
