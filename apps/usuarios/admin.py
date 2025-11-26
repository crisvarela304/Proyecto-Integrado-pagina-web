from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import PerfilUsuario

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
                raise ValidationError("El RUT es obligatorio para nuevos usuarios.")
            
            # Verificar si ya existe usuario con ese RUT
            if User.objects.filter(username=rut).exists():
                raise ValidationError(f"Ya existe un usuario con el RUT {rut}")
            
            # Validar que las contraseñas coincidan
            if password1 and password2 and password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")
            
            # Validar longitud mínima de contraseña
            if password1 and len(password1) < 6:
                raise ValidationError("La contraseña debe tener al menos 6 caracteres.")
                
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

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('rut', 'tipo_usuario', 'telefono', 'direccion', 'fecha_nacimiento', 'activo')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    form = QuickStudentCreationForm
    list_display = ('rut', 'nombre_completo', 'tipo_usuario', 'email_usuario', 'activo', 'created_at')
    list_filter = ('tipo_usuario', 'activo', 'created_at')
    search_fields = ('rut', 'user__first_name', 'user__last_name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('rut', 'first_name', 'last_name', 'tipo_usuario', 'fecha_nacimiento')
        }),
        ('Credenciales de Acceso', {
            'fields': ('email', 'password1', 'password2'),
            'description': 'Configuración del usuario para iniciar sesión en la página web.'
        }),
        ('Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si es edición, ocultar campos que solo se usan en creación
        if obj:
            # Eliminar campos de contraseña en edición
            if 'password1' in form.base_fields:
                del form.base_fields['password1']
            if 'password2' in form.base_fields:
                del form.base_fields['password2']
            # También ocultar nombre/apellido/email ya que se editan en User
            if 'first_name' in form.base_fields:
                del form.base_fields['first_name']
            if 'last_name' in form.base_fields:
                del form.base_fields['last_name']
            if 'email' in form.base_fields:
                del form.base_fields['email']
        return form

    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre Completo'
    
    def email_usuario(self, obj):
        return obj.user.email
    email_usuario.short_description = 'Email'

    def delete_model(self, request, obj):
        # Eliminar el usuario asociado (el perfil se elimina por CASCADE)
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        # Eliminar los usuarios asociados para cada perfil seleccionado
        for perfil in queryset:
            perfil.user.delete()

# Extender el admin de User para incluir el perfil
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'perfil__tipo_usuario')
    
    def tipo_usuario(self, obj):
        try:
            return obj.perfil.get_tipo_usuario_display()
        except:
            return 'Sin perfil'
    tipo_usuario.short_description = 'Tipo de Usuario'

# Re-registrar User con el nuevo admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Personalizar el admin site
admin.site.site_header = "Administración - Liceo Juan Bautista de Hualqui"
admin.site.site_title = "Administración del Liceo"
admin.site.index_title = "Panel de Administración"
