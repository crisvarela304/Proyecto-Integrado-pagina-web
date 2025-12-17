"""
Mixins de seguridad para las vistas de apoderados.
Controla el acceso a la información de los pupilos.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Pupilo


class ApoderadoRequiredMixin:
    """
    Mixin que verifica:
    1. El usuario tiene rol de 'apoderado'
    2. El estudiante consultado es pupilo del apoderado
    
    Uso:
        class MiVista(ApoderadoRequiredMixin, View):
            estudiante_url_kwarg = 'estudiante_id'  # nombre del param en URL
    """
    estudiante_url_kwarg = 'estudiante_id'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar autenticación
        if not request.user.is_authenticated:
            return redirect('usuarios:login')
        
        # Obtener perfil
        perfil = getattr(request.user, 'perfil', None)
        if not perfil:
            messages.error(request, 'No tienes un perfil asociado.')
            return redirect('home')
        
        # Verificar que sea apoderado
        if perfil.tipo_usuario != 'apoderado':
            messages.error(request, 'Esta sección es solo para apoderados.')
            return redirect('usuarios:panel')
        
        # Si se está consultando un estudiante específico, verificar acceso
        estudiante_id = kwargs.get(self.estudiante_url_kwarg)
        if estudiante_id:
            if not self._tiene_acceso_a_pupilo(perfil, estudiante_id):
                messages.error(request, 'No tienes acceso a la información de este estudiante.')
                return redirect('usuarios:panel')
        
        return super().dispatch(request, *args, **kwargs)
    
    def _tiene_acceso_a_pupilo(self, perfil_apoderado, estudiante_id):
        """Verifica si el apoderado tiene acceso al estudiante"""
        return Pupilo.objects.filter(
            apoderado=perfil_apoderado,
            estudiante__id=estudiante_id
        ).exists()
    
    def get_pupilos(self, request):
        """Retorna los pupilos del apoderado actual"""
        perfil = request.user.perfil
        return Pupilo.objects.filter(apoderado=perfil).select_related(
            'estudiante', 'estudiante__user'
        )


class AccesoEstudianteMixin:
    """
    Mixin más flexible que permite acceso si:
    - Es el propio estudiante
    - Es apoderado del estudiante
    - Es staff/admin
    """
    estudiante_url_kwarg = 'estudiante_id'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:login')
        
        estudiante_id = kwargs.get(self.estudiante_url_kwarg)
        if estudiante_id and not self._puede_ver_estudiante(request, estudiante_id):
            messages.error(request, 'No tienes permiso para ver esta información.')
            return redirect('usuarios:panel')
        
        return super().dispatch(request, *args, **kwargs)
    
    def _puede_ver_estudiante(self, request, estudiante_id):
        """Verifica si el usuario puede ver al estudiante"""
        user = request.user
        perfil = getattr(user, 'perfil', None)
        
        # Admin/Staff siempre puede
        if user.is_staff:
            return True
        
        if not perfil:
            return False
        
        # Es el propio estudiante
        if perfil.id == int(estudiante_id):
            return True
        
        # Es apoderado del estudiante
        if perfil.tipo_usuario == 'apoderado':
            return Pupilo.objects.filter(
                apoderado=perfil,
                estudiante__id=estudiante_id
            ).exists()
        
        return False
