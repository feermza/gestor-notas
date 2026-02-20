from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class EstadoChoices(models.TextChoices):
    """Estados posibles de una nota en el flujo formal."""
    INGRESADA = 'INGRESADA', 'Ingresada'
    EN_REVISION = 'EN_REVISION', 'En Revisión'
    ASIGNADA = 'ASIGNADA', 'Asignada'
    EN_PROCESO = 'EN_PROCESO', 'En Proceso'
    EN_ESPERA = 'EN_ESPERA', 'En Espera'
    DEVUELTA = 'DEVUELTA', 'Devuelta'
    RESUELTA = 'RESUELTA', 'Resuelta'
    ARCHIVADA = 'ARCHIVADA', 'Archivada'
    ANULADA = 'ANULADA', 'Anulada'


class PrioridadChoices(models.TextChoices):
    """Niveles de prioridad de una nota."""
    BAJA = 'BAJA', 'Baja'
    MEDIA = 'MEDIA', 'Media'
    ALTA = 'ALTA', 'Alta'
    URGENTE = 'URGENTE', 'Urgente'


class CanalIngresoChoices(models.TextChoices):
    """Canales por los que puede ingresar una nota."""
    EMAIL = 'EMAIL', 'Email'
    PRESENCIAL = 'PRESENCIAL', 'Presencial'
    TELEFONO = 'TELEFONO', 'Teléfono'
    SISTEMA = 'SISTEMA', 'Sistema'
    OTRO = 'OTRO', 'Otro'


class TipoEventoChoices(models.TextChoices):
    """Tipos de eventos que se registran en el historial."""
    CREACION = 'CREACION', 'Creación'
    CAMBIO_ESTADO = 'CAMBIO_ESTADO', 'Cambio de Estado'
    ASIGNACION = 'ASIGNACION', 'Asignación'
    REASIGNACION = 'REASIGNACION', 'Reasignación'
    ACTUALIZACION = 'ACTUALIZACION', 'Actualización'
    ANULACION = 'ANULACION', 'Anulación'
    ARCHIVADO = 'ARCHIVADO', 'Archivado'


class Nota(models.Model):
    """
    Modelo principal que representa una nota ingresada al sistema.
    Una nota nunca se borra físicamente, solo se anula con motivo.
    """
    numero_nota = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Nota',
        help_text='Formato: NOTA-YYYY-NNNN (generado automáticamente)'
    )
    fecha_ingreso = models.DateField(
        verbose_name='Fecha de Ingreso',
        help_text='Fecha en que la nota ingresó al sistema'
    )
    fecha_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Límite',
        help_text='Fecha límite para resolver la nota'
    )
    remitente = models.CharField(
        max_length=200,
        verbose_name='Remitente',
        help_text='Persona o entidad que envía la nota'
    )
    area_origen = models.CharField(
        max_length=100,
        verbose_name='Área de Origen',
        help_text='Área o departamento de origen de la nota'
    )
    tema = models.CharField(
        max_length=200,
        verbose_name='Tema',
        help_text='Tema o asunto principal de la nota'
    )
    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del contenido de la nota'
    )
    prioridad = models.CharField(
        max_length=10,
        choices=PrioridadChoices.choices,
        default=PrioridadChoices.MEDIA,
        verbose_name='Prioridad'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.INGRESADA,
        verbose_name='Estado'
    )
    canal_ingreso = models.CharField(
        max_length=20,
        choices=CanalIngresoChoices.choices,
        default=CanalIngresoChoices.PRESENCIAL,
        verbose_name='Canal de Ingreso'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_asignadas',
        verbose_name='Responsable',
        help_text='Usuario responsable de procesar la nota'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notas_creadas',
        verbose_name='Creado Por',
        help_text='Usuario que creó la nota en el sistema'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )
    anulada = models.BooleanField(
        default=False,
        verbose_name='Anulada',
        help_text='Indica si la nota ha sido anulada'
    )
    motivo_anulacion = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo de Anulación',
        help_text='Motivo por el cual la nota fue anulada'
    )

    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['responsable']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['numero_nota']),
        ]

    def __str__(self):
        return f"{self.numero_nota} - {self.tema}"

    def esta_atrasada(self):
        """Verifica si la nota está atrasada respecto a su fecha límite."""
        if self.fecha_limite and self.estado not in [
            EstadoChoices.RESUELTA,
            EstadoChoices.ARCHIVADA,
            EstadoChoices.ANULADA
        ]:
            from django.utils import timezone
            return timezone.now().date() > self.fecha_limite
        return False


class HistorialNota(models.Model):
    """
    Modelo inmutable que registra todos los cambios realizados en una nota.
    Este historial nunca se edita ni elimina.
    """
    nota = models.ForeignKey(
        Nota,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Nota'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='acciones_historial',
        verbose_name='Usuario',
        help_text='Usuario que realizó la acción'
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora',
        help_text='Fecha y hora en que se registró el evento'
    )
    tipo_evento = models.CharField(
        max_length=20,
        choices=TipoEventoChoices.choices,
        verbose_name='Tipo de Evento'
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        null=True,
        blank=True,
        verbose_name='Estado Anterior'
    )
    estado_nuevo = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        null=True,
        blank=True,
        verbose_name='Estado Nuevo'
    )
    responsable_anterior = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial_responsable_anterior',
        verbose_name='Responsable Anterior'
    )
    responsable_nuevo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial_responsable_nuevo',
        verbose_name='Responsable Nuevo'
    )
    descripcion_cambio = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descripción del Cambio',
        help_text='Descripción detallada del cambio realizado'
    )
    campos_modificados = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Campos Modificados',
        help_text='Diccionario JSON con los campos modificados y sus valores anteriores y nuevos'
    )

    class Meta:
        verbose_name = 'Historial de Nota'
        verbose_name_plural = 'Historial de Notas'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['nota', '-fecha_hora']),
            models.Index(fields=['usuario']),
        ]

    def __str__(self):
        return f"{self.nota.numero_nota} - {self.get_tipo_evento_display()} - {self.fecha_hora}"


class Adjunto(models.Model):
    """
    Modelo que representa un archivo adjunto asociado a una nota.
    """
    nota = models.ForeignKey(
        Nota,
        on_delete=models.CASCADE,
        related_name='adjuntos',
        verbose_name='Nota'
    )
    nombre_archivo = models.CharField(
        max_length=255,
        verbose_name='Nombre del Archivo',
        help_text='Nombre original del archivo'
    )
    ruta_almacenamiento = models.CharField(
        max_length=500,
        verbose_name='Ruta de Almacenamiento',
        help_text='Ruta donde se almacena el archivo en el servidor'
    )
    tipo_mime = models.CharField(
        max_length=100,
        verbose_name='Tipo MIME',
        help_text='Tipo MIME del archivo (ej: application/pdf, image/jpeg)'
    )
    tamaño_bytes = models.PositiveIntegerField(
        verbose_name='Tamaño en Bytes',
        help_text='Tamaño del archivo en bytes'
    )
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='adjuntos_subidos',
        verbose_name='Subido Por',
        help_text='Usuario que subió el archivo'
    )
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Subida'
    )

    class Meta:
        verbose_name = 'Adjunto'
        verbose_name_plural = 'Adjuntos'
        ordering = ['-fecha_subida']
        indexes = [
            models.Index(fields=['nota']),
        ]

    def __str__(self):
        return f"{self.nota.numero_nota} - {self.nombre_archivo}"

    def tamaño_formateado(self):
        """Retorna el tamaño del archivo formateado en KB o MB."""
        kb = self.tamaño_bytes / 1024
        if kb < 1024:
            return f"{kb:.2f} KB"
        mb = kb / 1024
        return f"{mb:.2f} MB"