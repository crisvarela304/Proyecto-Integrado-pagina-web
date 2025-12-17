from django import forms
from django.contrib.auth.models import User, Group
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

class ImportacionMasivaForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.filter(activo=True),
        label='Curso',
        required=True,
        help_text='Seleccione el curso al que se inscribirán los estudiantes.'
    )
    archivo = forms.FileField(
        label='Archivo de Estudiantes',
        help_text='Formatos soportados: .csv o .xlsx (Excel). Columnas requeridas: RUT, Nombres, Apellidos. Opcional: Email.'
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
            
            # Validar contraseña con validadores de Django
            if password1:
                from django.contrib.auth.password_validation import validate_password
                try:
                    validate_password(password1)
                except forms.ValidationError as e:
                    raise forms.ValidationError(e.messages)
                
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
            
            # Crear el usuario automáticamente
            is_profesor = (perfil.tipo_usuario == 'profesor')
            
            user = User.objects.create_user(
                username=rut,
                password=password,  # Usar la contraseña especificada
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_staff=False,  # Dar permisos de staff si es profesor
                is_superuser=False
            )
            
            # Si es profesor, agregar al grupo Profesores
            if is_profesor:
                try:
                    group = Group.objects.get(name='Profesores')
                    user.groups.add(group)
                except Group.DoesNotExist:
                    pass
                    
            perfil.user = user
            
        if commit:
            perfil.save()
        return perfil

class MatriculaForm(forms.Form):
    """Formulario unificado para matrícula rápida"""
    # Estudiante
    rut_estudiante = forms.CharField(
        label='RUT Estudiante', 
        widget=forms.TextInput(attrs={
            'class': 'form-control rut-input', 
            'placeholder': '12.345.678-9',
            'maxlength': '12'
        })
    )
    nombres = forms.CharField(label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email (Opcional)', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    # Curso
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.filter(activo=True).order_by('nivel', 'letra'),
        label='Curso a inscribir',
        required=False,
        empty_label="-- Solo registrar (sin matricular) --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Apoderado
    tiene_apoderado = forms.BooleanField(label='Registrar Apoderado', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'onchange': 'toggleApoderado(this)'}))
    rut_apoderado = forms.CharField(
        label='RUT Apoderado', 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control rut-input',
            'maxlength': '12'
        })
    )
    nombre_apoderado = forms.CharField(label='Nombre Completo Apoderado', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email_apoderado = forms.EmailField(label='Email Apoderado', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean_rut_estudiante(self):
        """Valida el formato y dígito verificador del RUT del estudiante"""
        from core.utils import validar_rut, formatear_rut
        rut = self.cleaned_data.get('rut_estudiante', '')
        if rut:
            rut = formatear_rut(rut)
            if not validar_rut(rut):
                raise forms.ValidationError('El RUT del estudiante no es válido.')
        return rut

    def clean_rut_apoderado(self):
        """Valida el formato y dígito verificador del RUT del apoderado"""
        from core.utils import validar_rut, formatear_rut
        rut = self.cleaned_data.get('rut_apoderado', '')
        if rut:
            rut = formatear_rut(rut)
            if not validar_rut(rut):
                raise forms.ValidationError('El RUT del apoderado no es válido.')
        return rut

    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('rut_estudiante')
        
        # Validar duplicados estudiante
        if rut and PerfilUsuario.objects.filter(rut=rut).exists():
            raise forms.ValidationError("Ya existe un estudiante con este RUT.")
            
        # Validar apoderado si se marca
        if cleaned_data.get('tiene_apoderado'):
            if not cleaned_data.get('rut_apoderado'):
                self.add_error('rut_apoderado', 'El RUT del apoderado es obligatorio si se marca la opción.')
            if not cleaned_data.get('nombre_apoderado'):
                self.add_error('nombre_apoderado', 'El nombre del apoderado es obligatorio.')
        
        return cleaned_data

