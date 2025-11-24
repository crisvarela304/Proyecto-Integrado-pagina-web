from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('rut', 'tipo_usuario', 'telefono', 'direccion', 'fecha_nacimiento', 'activo')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'tipo_usuario', 'email_usuario', 'activo', 'created_at')
    list_filter = ('tipo_usuario', 'activo', 'created_at')
    search_fields = ('rut', 'user__first_name', 'user__last_name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre Completo'
    
    def email_usuario(self, obj):
        return obj.user.email
    email_usuario.short_description = 'Email'



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
