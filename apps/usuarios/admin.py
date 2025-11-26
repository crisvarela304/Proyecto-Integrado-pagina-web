from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
import io
from .models import PerfilUsuario
from .forms import QuickStudentCreationForm, CSVImportForm
from academico.models import InscripcionCurso



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
    
    change_list_template = "admin/usuarios/perfilusuario/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='usuarios_perfilusuario_import_csv'),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                curso = form.cleaned_data['curso'] # Obtener el curso seleccionado
                
                # Intentar decodificar con diferentes encodings
                decoded_file = None
                encodings = ['utf-8-sig', 'latin-1', 'cp1252']
                
                file_data = csv_file.read()
                
                for encoding in encodings:
                    try:
                        decoded_file = file_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not decoded_file:
                    messages.error(request, "No se pudo decodificar el archivo. Asegúrese de que sea un CSV válido (UTF-8 o Latin-1).")
                    return redirect("admin:usuarios_perfilusuario_changelist")

                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=';') # Try semicolon first
                
                # Check if headers are correct, if not try comma
                if 'RUT' not in reader.fieldnames:
                    io_string.seek(0)
                    reader = csv.DictReader(io_string, delimiter=',')
                
                created_count = 0
                errors = []
                
                for row in reader:
                    try:
                        rut = row.get('RUT', '').strip()
                        nombres = row.get('Nombres', '').strip()
                        apellidos = row.get('Apellidos', '').strip()
                        email = row.get('Email', '').strip()
                        
                        if not rut or not nombres or not apellidos:
                            continue
                            
                        # Check if user exists
                        if User.objects.filter(username=rut).exists():
                            errors.append(f"El usuario con RUT {rut} ya existe.")
                            continue
                            
                        # Check if profile with RUT exists (to avoid unique constraint failed)
                        if PerfilUsuario.objects.filter(rut=rut).exists():
                            errors.append(f"El RUT {rut} ya está registrado en un perfil existente.")
                            continue
                            
                        # Create User
                        # Password: First 6 digits of RUT (without dots)
                        rut_limpio = rut.replace('.', '')
                        password = rut_limpio[:6] 
                        
                        if not email:
                            email = f"{rut}@liceo.cl"
                            
                        user = User.objects.create_user(
                            username=rut,
                            password=password,
                            first_name=nombres,
                            last_name=apellidos,
                            email=email,
                            is_staff=False
                        )
                        
                        # Create Perfil
                        PerfilUsuario.objects.create(
                            user=user,
                            rut=rut,
                            tipo_usuario='estudiante',
                            activo=True
                        )
                        
                        # Inscribir en el curso seleccionado
                        InscripcionCurso.objects.create(
                            estudiante=user,
                            curso=curso,
                            año=2024, # Podríamos hacerlo dinámico, pero por ahora 2024
                            estado='activo'
                        )
                        
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f"Error en fila {row}: {str(e)}")
                
                if created_count > 0:
                    messages.success(request, f"Se importaron {created_count} estudiantes al curso {curso} exitosamente.")
                
                if errors:
                    messages.warning(request, f"Hubo errores en {len(errors)} registros: " + "; ".join(errors[:5]))
                    
                return redirect("admin:usuarios_perfilusuario_changelist")
        else:
            form = CSVImportForm()
            
        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Importar Alumnos (CSV)',
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
            'has_permission': True,
        }
        return render(request, "admin/usuarios/perfilusuario/import_csv.html", context)

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

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.fieldsets
        
        return (
            ('Información Personal', {
                'fields': ('rut', 'tipo_usuario', 'fecha_nacimiento')
            }),
            ('Contacto', {
                'fields': ('telefono', 'direccion')
            }),
            ('Estado', {
                'fields': ('activo',)
            }),
        )

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)
        # Si es edición, usar un formulario modificado que no requiera los campos de creación
        if obj:
            class PerfilChangeForm(Form):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # Eliminar campos que solo son para creación
                    fields_to_remove = ['first_name', 'last_name', 'email', 'password1', 'password2']
                    for field in fields_to_remove:
                        if field in self.fields:
                            del self.fields[field]
            return PerfilChangeForm
        return Form

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
