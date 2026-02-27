"""
Backend de autenticación personalizado que permite login con legajo.
"""
from django.contrib.auth.backends import BaseBackend
from .models import Usuario


class LegajoBackend(BaseBackend):
    """
    Backend de autenticación que permite iniciar sesión usando el legajo
    en lugar del username.
    """
    
    def authenticate(self, request, legajo=None, password=None, **kwargs):
        """
        Autentica un usuario usando legajo y password.
        
        Args:
            request: Request HTTP (puede ser None)
            legajo: Número de legajo del usuario
            password: Contraseña del usuario
            
        Returns:
            Usuario si las credenciales son válidas, None en caso contrario
        """
        if legajo is None or password is None:
            return None
        
        try:
            usuario = Usuario.objects.get(legajo=legajo)
        except Usuario.DoesNotExist:
            return None
        
        # Verificar password y que el usuario esté activo
        if usuario.check_password(password) and usuario.is_active:
            return usuario
        
        return None
    
    def get_user(self, user_id):
        """
        Retorna un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario si existe, None en caso contrario
        """
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
