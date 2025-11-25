from django.contrib import admin
from .models import ConfiguracionSistema

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Panel de administración para configuraciones del sistema"""
    list_display = ('clave', 'valor_preview', 'descripcion', 'activo', 'created_at')
    list_filter = ('activo', 'created_at')
    search_fields = ('clave', 'descripcion')
    readonly_fields = ('created_at', 'updated_at')
    
    def valor_preview(self, obj):
        return obj.valor[:50] + '...' if len(obj.valor) > 50 else obj.valor
    valor_preview.short_description = 'Valor'
