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
        fields = ['telefono', 'direccion']

class PasswordChangeForm(AuthPasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Contraseña actual")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="Nueva contraseña")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar nueva contraseña")