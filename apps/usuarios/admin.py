from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import PerfilUsuario

class QuickStudentCreationForm(forms.ModelForm):
    """Formulario para creación rápida de estudiantes"""
    first_name = forms.CharField(label='Nombre', max_length=150, required=False)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=False)
    
    class Meta:
        model = PerfilUsuario
        fields = ('rut', 'tipo_usuario', 'telefono', 'direccion', 'fecha_nacimiento', 'activo')

    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('rut')
        
        # Si no hay usuario seleccionado (es creación nueva)
        if not self.instance.pk and not self.initial.get('user'):
            if not rut:
                raise ValidationError("El RUT es obligatorio para nuevos usuarios.")
            
            # Verificar si ya existe usuario con ese RUT
            if User.objects.filter(username=rut).exists():
                raise ValidationError(f"Ya existe un usuario con el RUT {rut}")
                
        return cleaned_data

    def save(self, commit=True):
        perfil = super().save(commit=False)
        
        # Si es un perfil nuevo y no tiene usuario asignado
        if not perfil.user_id:
            rut = self.cleaned_data.get('rut')
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            
            # La contraseña serán los primeros números del RUT (antes del guion)
            password = rut.split('-')[0]
            
            # Crear el usuario automáticamente
            user = User.objects.create_user(
                username=rut,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=f"{rut}@liceo.cl"  # Email temporal
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
        ('Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si es edición, ocultar campos de nombre/apellido ya que se editan en User
        if obj:
            if 'first_name' in form.base_fields:
                del form.base_fields['first_name']
            if 'last_name' in form.base_fields:
                del form.base_fields['last_name']
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
