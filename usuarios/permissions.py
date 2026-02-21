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
    """Solo usuarios con rol ADMIN."""
    message = 'Solo los administradores pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol == RolChoices.ADMIN
        )


class EsDirectorOJefe(BasePermission):
    """Usuarios con rol DIRECTOR o JEFE."""
    message = 'Se requiere rol Director o Jefe.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol in (RolChoices.DIRECTOR, RolChoices.JEFE)
        )


class EsDirectorJefeOAdmin(BasePermission):
    """Usuarios con rol DIRECTOR, JEFE o ADMIN."""
    message = 'Se requiere rol Director, Jefe o Administrador.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.rol in (
                RolChoices.ADMIN,
                RolChoices.DIRECTOR,
                RolChoices.JEFE,
            )
        )


class PuedeCrearNota(BasePermission):
    """Roles que pueden crear notas: ADMIN, DIRECTOR, JEFE, EMPLEADO."""
    message = 'No tiene permiso para crear notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_crear_nota()
        )


class PuedeVerTodasLasNotas(BasePermission):
    """Roles que pueden ver todas las notas: ADMIN, DIRECTOR, JEFE, SOLO_LECTURA."""
    message = 'No tiene permiso para ver el listado de notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_ver_todas_las_notas()
        )


class PuedeAsignarNota(BasePermission):
    """Roles que pueden asignar o reasignar notas: ADMIN, DIRECTOR, JEFE."""
    message = 'No tiene permiso para asignar o reasignar notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_asignar_nota()
        )


class PuedeAnularNota(BasePermission):
    """Roles que pueden anular notas: ADMIN, DIRECTOR."""
    message = 'Solo Director o Administrador pueden anular notas.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Usuario)
            and request.user.puede_anular_nota()
        )


class PuedeVerNotas(BasePermission):
    """
    Permiso para list/retrieve: puede ver todas (ADMIN, DIRECTOR, JEFE, SOLO_LECTURA)
    o es EMPLEADO (verá solo las suyas; el queryset se filtra en la vista).
    """
    message = 'No tiene permiso para ver notas.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not isinstance(request.user, Usuario):
            return False
        # Puede ver todas O es empleado (ve solo asignadas/propias)
        return (
            request.user.puede_ver_todas_las_notas()
            or request.user.rol == RolChoices.EMPLEADO
        )
