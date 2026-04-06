from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class RolChoices(models.TextChoices):
    """Roles de negocio para quienes tienen acceso al sistema."""

    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    SUPERVISOR = "SUPERVISOR", "Supervisor"
    OPERADOR = "OPERADOR", "Operador"
    CONSULTOR = "CONSULTOR", "Consultor"


class SituacionRevistaChoices(models.TextChoices):
    PLANTA = "PLANTA", "Planta permanente"
    CONTRATADO = "CONTRATADO", "Contratado"
    PASANTE = "PASANTE", "Pasante"
    OTRO = "OTRO", "Otro"


class AgenteManager(BaseUserManager):
    """Manager: login por `legajo` en lugar de username."""

    def create_user(self, legajo, email=None, password=None, **extra_fields):
        if not legajo:
            raise ValueError("El legajo es obligatorio")
        if email:
            email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        if password:
            extra_fields.setdefault("usuario_sistema", True)
        user = self.model(legajo=legajo, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, legajo, email=None, password=None, **extra_fields):
        if not email:
            email = f"{legajo}@superuser.local"
        email = self.normalize_email(email)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("usuario_sistema", True)
        extra_fields.setdefault("rol", RolChoices.ADMINISTRADOR)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True.")
        return self.create_user(legajo, email, password, **extra_fields)


class Agente(AbstractUser):
    """
    Persona institucional unificada (AUTH_USER_MODEL).
    Sin acceso al sistema: usuario_sistema=False, contraseña no utilizable,
    is_active=False, rol=None.
    """

    username = None
    legajo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Legajo",
        help_text="Número de legajo (usado para iniciar sesión)",
    )
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    dni = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DNI",
        help_text="Documento Nacional de Identidad",
    )
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento",
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Email",
    )
    sector = models.ForeignKey(
        "notas.Sector",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agentes",
        verbose_name="Sector",
    )
    cargo = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Cargo",
    )
    fecha_ingreso = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de ingreso",
    )
    situacion_revista = models.CharField(
        max_length=30,
        choices=SituacionRevistaChoices.choices,
        null=True,
        blank=True,
        verbose_name="Situación de revista",
    )
    agente_activo = models.BooleanField(
        default=True,
        verbose_name="Agente activo",
        help_text="Indica que el agente es personal activo de la institución.",
    )
    usuario_sistema = models.BooleanField(
        default=False,
        verbose_name="Usuario del sistema",
        help_text="Indica que el agente tiene acceso al sistema de gestión. "
        "Se activa exclusivamente desde el sistema, nunca desde el admin.",
    )
    activo_rrhh = models.BooleanField(
        default=True,
        verbose_name="Activo (RRHH)",
        help_text="Vigencia en nómina / legajo; independiente del acceso al sistema (is_active).",
    )
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        null=True,
        blank=True,
        verbose_name="Rol",
        help_text="Sin rol = sin permisos de aplicación (solo ficha institucional).",
    )
    debe_cambiar_password = models.BooleanField(
        default=False,
        verbose_name="Debe cambiar contraseña",
        help_text="Si True, el sistema obliga al agente a cambiar su contraseña en el próximo login.",
    )

    USERNAME_FIELD = "legajo"
    REQUIRED_FIELDS = ["apellido", "nombres"]

    objects = AgenteManager()

    class Meta:
        verbose_name = "Agente"
        verbose_name_plural = "Agentes"
        ordering = ["apellido", "nombres"]

    def __str__(self):
        return f"{self.apellido}, {self.nombres} (Leg. {self.legajo})"

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombres}"

    @property
    def activo(self):
        return self.is_active

    @activo.setter
    def activo(self, value):
        self.is_active = value

    @property
    def ultimo_ingreso(self):
        return self.last_login

    @ultimo_ingreso.setter
    def ultimo_ingreso(self, value):
        self.last_login = value

    def puede_crear_nota(self):
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR,
            RolChoices.OPERADOR,
        ]

    def puede_asignar(self):
        return self.rol in [RolChoices.ADMINISTRADOR, RolChoices.SUPERVISOR]

    def puede_anular(self):
        return self.rol in [RolChoices.ADMINISTRADOR, RolChoices.SUPERVISOR]

    def es_consultor(self):
        return self.rol == RolChoices.CONSULTOR

    def puede_ver_todas_las_notas(self):
        return self.rol in [
            RolChoices.ADMINISTRADOR,
            RolChoices.SUPERVISOR,
            RolChoices.CONSULTOR,
            RolChoices.OPERADOR,
        ]

    def get_rol_display(self):
        if not self.rol:
            return ""
        return dict(RolChoices.choices).get(self.rol, str(self.rol))


class DocumentoLegajo(models.Model):
    """
    Vincula un adjunto de una nota al legajo personal virtual del agente.
    `related_name='documentos_legajo_virtual'` se mantiene para no colisionar con
    notas.LegajoDocumento (related_name documentos_legajo sobre el mismo usuario).
    """

    agente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_legajo_virtual",
        verbose_name="Agente",
    )
    nota = models.ForeignKey(
        "notas.Nota",
        on_delete=models.PROTECT,
        related_name="documentos_legajo_virtual",
        verbose_name="Nota",
    )
    adjunto = models.ForeignKey(
        "notas.Adjunto",
        on_delete=models.PROTECT,
        related_name="documentos_legajo_virtual",
        verbose_name="Adjunto",
    )
    archivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_legajo_archivados",
        verbose_name="Archivado por",
    )
    fecha_archivo = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de archivo",
    )

    class Meta:
        ordering = ["-fecha_archivo"]
        verbose_name = "Documento de legajo"
        verbose_name_plural = "Documentos de legajo"

    def __str__(self):
        return f"{self.agente} - {self.nota.numero_nota}"
