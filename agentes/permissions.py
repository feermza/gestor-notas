"""
Permisos DRF por rol de negocio (agentes.Agente).
"""
from rest_framework.permissions import BasePermission

from .models import Agente, RolChoices


class EstaAutenticado(BasePermission):
    message = "Debe iniciar sesión para realizar esta acción."

    def has_permission(self, request, view):
        return request.user.is_authenticated


class EsAdmin(BasePermission):
    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.rol == RolChoices.ADMINISTRADOR
        )


class IsAdministrador(BasePermission):
    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "ADMINISTRADOR"
        )


class EsSupervisor(BasePermission):
    message = "Se requiere rol Supervisor."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.rol == RolChoices.SUPERVISOR
        )


class EsSupervisorOAdmin(BasePermission):
    message = "Se requiere rol Supervisor o Administrador."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.rol
            in (
                RolChoices.ADMINISTRADOR,
                RolChoices.SUPERVISOR,
            )
        )


class EsDirectorJefeOAdmin(BasePermission):
    message = "Se requiere rol Supervisor o Administrador."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.rol
            in (
                RolChoices.ADMINISTRADOR,
                RolChoices.SUPERVISOR,
            )
        )


class PuedeCrearNota(BasePermission):
    message = "No tiene permiso para crear notas."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.puede_crear_nota()
        )


class PuedeVerTodasLasNotas(BasePermission):
    message = "No tiene permiso para ver el listado de notas."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.puede_ver_todas_las_notas()
        )


class PuedeAsignarNota(BasePermission):
    message = "No tiene permiso para asignar o reasignar notas."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.puede_asignar()
        )


class PuedeAnularNota(BasePermission):
    message = "Solo Supervisor o Administrador pueden anular notas."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, Agente)
            and request.user.puede_anular()
        )


class PuedeVerNotas(BasePermission):
    message = "No tiene permiso para ver notas."

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not isinstance(request.user, Agente):
            return False
        return (
            request.user.puede_ver_todas_las_notas()
            or request.user.rol == RolChoices.OPERADOR
        )
