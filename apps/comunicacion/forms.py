from django import forms
from .models import Noticia

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'bajada', 'cuerpo', 'portada', 'categoria', 'es_publica', 'destacado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia'}),
            'bajada': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Resumen o bajada'}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'portada': forms.FileInput(attrs={'class': 'form-control'}),
            'es_publica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'es_publica': 'Publicar inmediatamente',
            'destacado': 'Destacar en portada'
        }
