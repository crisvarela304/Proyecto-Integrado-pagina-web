from django import forms

from .models import Asignatura, Curso, Calificacion, HorarioClases


class SeleccionCursoAsignaturaForm(forms.Form):
    """Formulario para que el profesor elija curso y asignatura."""
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        label='Curso',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    asignatura = forms.ModelChoiceField(
        queryset=Asignatura.objects.none(),
        label='Asignatura',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        super().__init__(*args, **kwargs)
        if profesor:
            cursos_ids = HorarioClases.objects.filter(
                profesor=profesor
            ).values_list('curso_id', flat=True).distinct()
            asignaturas_ids = HorarioClases.objects.filter(
                profesor=profesor
            ).values_list('asignatura_id', flat=True).distinct()
            self.fields['curso'].queryset = Curso.objects.filter(id__in=cursos_ids)
            self.fields['asignatura'].queryset = Asignatura.objects.filter(id__in=asignaturas_ids)


class CalificacionForm(forms.ModelForm):
    """Formulario para registrar o editar una calificación."""

    class Meta:
        model = Calificacion
        fields = [
            'tipo_evaluacion',
            'semestre',
            'numero_evaluacion',
            'fecha_evaluacion',
            'nota',
            'descripcion',
        ]
        widgets = {
            'fecha_evaluacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la evaluación'}),
            'nota': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control', 'min': 1, 'max': 7}),
            'numero_evaluacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
