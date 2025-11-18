from django.contrib import admin
from django.utils.html import format_html
from .models import Noticia, CategoriaNoticia

@admin.register(CategoriaNoticia)
class CategoriaNoticiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_preview', 'activa', 'created_at')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    @admin.display(description='Color')
    def color_preview(self, obj):
        return format_html(
            '<div style="width:20px;height:20px;background-color:{};border-radius:3px;display:inline-block;"></div> {}',
            obj.color,
            obj.color
        )

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'autor_display', 'es_publica', 'destacado', 'urgente', 'visitas', 'creado')
    list_filter = ('categoria', 'es_publica', 'destacado', 'urgente', 'creado', 'autor')
    search_fields = ('titulo', 'bajada', 'cuerpo', 'autor__first_name', 'autor__last_name', 'autor__username')
    readonly_fields = ('creado', 'actualizado', 'visitas')
    list_per_page = 25
    date_hierarchy = 'creado'
    ordering = ('-destacado', '-urgente', '-creado')
    
    # Campos del formulario
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'bajada', 'cuerpo', 'portada')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'autor')
        }),
        ('Opciones de Publicación', {
            'fields': ('es_publica', 'destacado', 'urgente')
        }),
        ('Metadatos', {
            'fields': ('visitas', 'creado', 'actualizado'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Autor')
    def autor_display(self, obj):
        if obj.autor:
            return f"{obj.autor.get_full_name() or obj.autor.username}"
        return "Sin autor"
    
    def save_model(self, request, obj, form, change):
        if not obj.autor:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(autor=request.user)

# Acciones personalizadas
@admin.action(description='Marcar como destacadas')
def marcar_destacadas(modeladmin, request, queryset):
    queryset.update(destacado=True)

@admin.action(description='Marcar como urgentes')
def marcar_urgentes(modeladmin, request, queryset):
    queryset.update(urgente=True)

@admin.action(description='Publicar seleccionadas')
def publicar_seleccionadas(modeladmin, request, queryset):
    queryset.update(es_publica=True)

@admin.action(description='Despublicar seleccionadas')
def despublicar_seleccionadas(modeladmin, request, queryset):
    queryset.update(es_publica=False)

# Agregar acciones al admin
NoticiaAdmin.actions = [marcar_destacadas, marcar_urgentes, publicar_seleccionadas, despublicar_seleccionadas]
