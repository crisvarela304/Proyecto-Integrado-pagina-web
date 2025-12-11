from django import forms

class CargaMasivaForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        help_text='Sube el archivo siguiendo la plantilla oficial.',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if not archivo.name.endswith('.xlsx'):
                raise forms.ValidationError("El archivo debe ser un Excel (.xlsx)")
        return archivo
