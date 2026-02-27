from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class RolChoices(models.TextChoices):
    """Opciones de roles de usuario en el sistema."""
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    SUPERVISOR = 'SUPERVISOR', 'Supervisor'
    OPERADOR = 'OPERADOR', 'Operador'
    CONSULTOR = 'CONSULTOR', 'Consultor'


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario que usa legajo en lugar de username."""
    
    def create_user(self, legajo, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el legajo y email dados.
        
        Args:
            legajo: Número de legajo del usuario (obligatorio)
            email: Email del usuario (obligatorio)
            password: Contraseña del usuario (opcional)
            **extra_fields: Campos adicionales del modelo
            
        Returns:
            Usuario: Usuario creado
        """
        if not legajo:
            raise ValueError('El legajo es obligatorio')
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(legajo=legajo, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, legajo, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el legajo y email dados.
        
        Args:
            legajo: Número de legajo del superusuario
            email: Email del superusuario
            password: Contraseña del superusuario
            **extra_fields: Campos adicionales del modelo
            
        Returns:
            Usuario: Superusuario creado
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ADMINISTRADOR')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(legajo, email, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    El usuario inicia sesión con su legajo en lugar de username.
    """
    username = None
    # Campo de login: legajo reemplaza a username
    legajo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Legajo',
        help_text='Número de legajo del usuario (usado para login)'
    )
    
    # Campos de identificación personal
    apellido = models.CharField(
        max_length=100,
        verbose_name='Apellido'
    )
    nombres = models.CharField(
        max_length=100,
        verbose_name='Nombres'
    )
    dni = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name='DNI',
        help_text='Documento Nacional de Identidad'
    )
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )
    
    # Email único
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    
    # Rol del usuario
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.OPERADOR,
        verbose_name='Rol',
        help_text='Rol del usuario en el sistema'
    )
    
    # Nota: is_active y last_login vienen de AbstractUser
    # Usamos propiedades para exponerlos como 'activo' y 'ultimo_ingreso'
    
    # Configuración de login
    USERNAME_FIELD = 'legajo'
    REQUIRED_FIELDS = ['apellido', 'nombres', 'email']
    
    # Manager personalizado que usa legajo en lugar de username
    objects = UsuarioManager()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['apellido', 'nombres']
    
    def __str__(self):
        """Retorna formato: 'Apellido, Nombres (legajo)'."""
        return f"{self.apellido}, {self.nombres} ({self.legajo})"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo en formato 'Apellido, Nombres'."""
        return f"{self.apellido}, {self.nombres}"
    
    @property
    def activo(self):
        """Mapea is_active de Django a activo."""
        return self.is_active
    
    @activo.setter
    def activo(self, value):
        """Sincroniza activo con is_active."""
        self.is_active = value
    
    @property
    def ultimo_ingreso(self):
        """Mapea last_login de Django a ultimo_ingreso."""
        return self.last_login
    
    @ultimo_ingreso.setter
    def ultimo_ingreso(self, value):
        """Sincroniza ultimo_ingreso con last_login."""
        self.last_login = value
    
    def puede_crear_nota(self):
        """Verifica si el usuario puede crear notas."""
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR,
            RolChoices.OPERADOR
        ]
    
    def puede_asignar(self):
        """Verifica si el usuario puede asignar o reasignar notas."""
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR
        ]
    
    def puede_anular(self):
        """Verifica si el usuario puede anular notas."""
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR
        ]
    
    def es_consultor(self):
        """Verifica si el usuario es consultor (solo lectura)."""
        return self.rol == RolChoices.CONSULTOR
    
    def puede_ver_todas_las_notas(self):
        """Verifica si el usuario puede ver todas las notas."""
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR,
            RolChoices.CONSULTOR
        ]
    
    def get_rol_display(self):
        """Retorna el display del rol."""
        return dict(RolChoices.choices).get(self.rol, self.rol)
