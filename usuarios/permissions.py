"""
Clases de permisos para el control de acceso por rol.
Usan BasePermission de Django REST Framework.
"""
from rest_framework.permissions import BasePermission

from .models import Usuario, RolChoices


class EstaAutenticado(BasePermission):
    """Verifica que exista una sesión activa (usuario autenticado)."""
    message = 'Debe iniciar sesión para realizar esta acción.'

    def has_permission(self, request, view):
        return request.user.is_authenticated


class EsAdmin(BasePermission):
    """Solo usuarios con rol ADMINISTRADOR."""
    message = 'Solo los administradores pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol == RolChoices.ADMINISTRADOR
        )


class EsSupervisor(BasePermission):
    """Usuarios con rol SUPERVISOR."""
    message = 'Se requiere rol Supervisor.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol == RolChoices.SUPERVISOR
        )


class EsSupervisorOAdmin(BasePermission):
    """Usuarios con rol SUPERVISOR o ADMINISTRADOR."""
    message = 'Se requiere rol Supervisor o Administrador.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol in (
                RolChoices.ADMINISTRADOR,
                RolChoices.SUPERVISOR,
            )
        )


class EsDirectorJefeOAdmin(BasePermission):
    """Usuarios con rol SUPERVISOR o ADMINISTRADOR (compatibilidad con código existente)."""
    message = 'Se requiere rol Supervisor o Administrador.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol in (
                RolChoices.ADMINISTRADOR,
                RolChoices.SUPERVISOR,
            )
        )


class PuedeCrearNota(BasePermission):
    """Roles que pueden crear notas: ADMINISTRADOR, SUPERVISOR, OPERADOR."""
    message = 'No tiene permiso para crear notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_crear_nota()
        )


class PuedeVerTodasLasNotas(BasePermission):
    """Roles que pueden ver todas las notas: ADMINISTRADOR, SUPERVISOR, CONSULTOR."""
    message = 'No tiene permiso para ver el listado de notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_ver_todas_las_notas()
        )


class PuedeAsignarNota(BasePermission):
    """Roles que pueden asignar o reasignar notas: ADMINISTRADOR, SUPERVISOR."""
    message = 'No tiene permiso para asignar o reasignar notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_asignar()
        )


class PuedeAnularNota(BasePermission):
    """Roles que pueden anular notas: ADMINISTRADOR, SUPERVISOR."""
    message = 'Solo Supervisor o Administrador pueden anular notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_anular()
        )


class PuedeVerNotas(BasePermission):
    """
    Permiso para list/retrieve: puede ver todas (ADMINISTRADOR, SUPERVISOR, CONSULTOR)
    o es OPERADOR (verá solo las suyas; el queryset se filtra en la vista).
    """
    message = 'No tiene permiso para ver notas.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not isinstance(request.user, Usuario):
            return False
        # Puede ver todas O es operador (ve solo asignadas/propias)
        return (
            request.user.puede_ver_todas_las_notas()
            or request.user.rol == RolChoices.OPERADOR
        )
