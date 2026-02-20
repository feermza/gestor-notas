from django.contrib.auth.models import AbstractUser
from django.db import models


class RolChoices(models.TextChoices):
    """Opciones de roles de usuario en el sistema."""
    ADMIN = 'ADMIN', 'Administrador'
    DIRECTOR = 'DIRECTOR', 'Director'
    JEFE = 'JEFE', 'Jefe'
    EMPLEADO = 'EMPLEADO', 'Empleado'
    SOLO_LECTURA = 'SOLO_LECTURA', 'Solo Lectura'


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Agrega el campo 'rol' para gestionar los permisos en el sistema.
    """
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.EMPLEADO,
        verbose_name='Rol',
        help_text='Rol del usuario en el sistema'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name', 'username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    def es_admin(self):
        """Verifica si el usuario es administrador."""
        return self.rol == RolChoices.ADMIN

    def es_director(self):
        """Verifica si el usuario es director."""
        return self.rol == RolChoices.DIRECTOR

    def es_jefe(self):
        """Verifica si el usuario es jefe."""
        return self.rol == RolChoices.JEFE

    def es_empleado(self):
        """Verifica si el usuario es empleado."""
        return self.rol == RolChoices.EMPLEADO

    def es_solo_lectura(self):
        """Verifica si el usuario tiene solo permisos de lectura."""
        return self.rol == RolChoices.SOLO_LECTURA

    def puede_crear_nota(self):
        """Verifica si el usuario puede crear notas."""
        return self.rol in [
            RolChoices.ADMIN,
            RolChoices.DIRECTOR,
            RolChoices.JEFE,
            RolChoices.EMPLEADO
        ]

    def puede_asignar_nota(self):
        """Verifica si el usuario puede asignar o reasignar notas."""
        return self.rol in [
            RolChoices.ADMIN,
            RolChoices.DIRECTOR,
            RolChoices.JEFE
        ]

    def puede_anular_nota(self):
        """Verifica si el usuario puede anular notas."""
        return self.rol in [
            RolChoices.ADMIN,
            RolChoices.DIRECTOR
        ]

    def puede_ver_todas_las_notas(self):
        """Verifica si el usuario puede ver todas las notas."""
        return self.rol in [
            RolChoices.ADMIN,
            RolChoices.DIRECTOR,
            RolChoices.JEFE,
            RolChoices.SOLO_LECTURA
        ]