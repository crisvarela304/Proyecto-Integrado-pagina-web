from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario
from django.contrib.auth.forms import PasswordChangeForm as AuthPasswordChangeForm

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_password_confirm(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password_confirm']:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cd['password_confirm']

class PerfilUsuarioRegistrationForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['rut', 'tipo_usuario']

class LoginForm(forms.Form):
    rut_o_username = forms.CharField(label="RUT o Usuario")
    password = forms.CharField(widget=forms.PasswordInput)

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

class PerfilUsuarioEditForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['telefono', 'telefono_estudiante', 'telefono_apoderado', 'direccion', 'foto_perfil']

class PasswordChangeForm(AuthPasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Contraseña actual")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="Nueva contraseña")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar nueva contraseña")

from academico.models import Curso

class CSVImportForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.filter(activo=True),
        label='Curso',
        required=True,
        help_text='Seleccione el curso al que se inscribirán los estudiantes.'
    )
    csv_file = forms.FileField(
        label='Archivo CSV',
        help_text='El archivo debe tener las columnas: RUT, Nombres, Apellidos, Email (opcional). Separado por comas o punto y coma.'
    )

class QuickStudentCreationForm(forms.ModelForm):
    """Formulario para creación rápida de usuarios"""
    first_name = forms.CharField(label='Nombre', max_length=150, required=True)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=True)
    email = forms.EmailField(label='Email', required=False, help_text='Opcional. Si no se especifica, se generará automáticamente.')
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese contraseña'}),
        required=True,
        help_text='Contraseña para que el usuario inicie sesión.'
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme contraseña'}),
        required=True,
        help_text='Ingrese la misma contraseña para verificación.'
    )
    
    class Meta:
        model = PerfilUsuario
        fields = ('rut', 'tipo_usuario', 'telefono', 'direccion', 'fecha_nacimiento', 'activo')

    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('rut')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Si no hay usuario seleccionado (es creación nueva)
        if not self.instance.pk and not self.initial.get('user'):
            if not rut:
                raise forms.ValidationError("El RUT es obligatorio para nuevos usuarios.")
            
            # Verificar si ya existe usuario con ese RUT
            if User.objects.filter(username=rut).exists():
                raise forms.ValidationError(f"Ya existe un usuario con el RUT {rut}")
            
            # Validar que las contraseñas coincidan
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
            
            # Validar longitud mínima de contraseña
            if password1 and len(password1) < 6:
                raise forms.ValidationError("La contraseña debe tener al menos 6 caracteres.")
                
        return cleaned_data

    def save(self, commit=True):
        perfil = super().save(commit=False)
        
        # Si es un perfil nuevo y no tiene usuario asignado
        if not perfil.user_id:
            rut = self.cleaned_data.get('rut')
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            email = self.cleaned_data.get('email', '')
            password = self.cleaned_data.get('password1')
            
            # Si no hay email, generar uno automáticamente
            if not email:
                email = f"{rut}@liceo.cl"
            
            # Crear el usuario automáticamente (usuarios NORMALES, sin permisos de staff)
            user = User.objects.create_user(
                username=rut,
                password=password,  # Usar la contraseña especificada
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_staff=False,  # NO dar permisos de staff
                is_superuser=False  # NO dar permisos de superusuario
            )
            perfil.user = user
            
        if commit:
            perfil.save()
        return perfil
