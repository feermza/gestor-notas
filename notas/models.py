from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone


# --- Sectores y agentes ---

class Sector(models.Model):
    """Sector o área institucional (ej: RRHH=150, Secretaría Académica=129)."""
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    numero = models.IntegerField(
        unique=True,
        verbose_name='Número',
        help_text='Identificador institucional del sector'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'
        ordering = ['numero']

    def __str__(self):
        return f"{self.nombre} ({self.numero})"


class Agente(models.Model):
    """
    Persona de la institución (puede o no tener acceso al sistema).
    Agente != Usuario: un agente puede no tener login.
    """
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    legajo_numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de legajo'
    )
    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agentes',
        verbose_name='Sector'
    )
    cargo = models.CharField(max_length=150, blank=True, verbose_name='Cargo')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agente',
        verbose_name='Usuario',
        help_text='Usuario del sistema asociado (si tiene acceso)'
    )

    class Meta:
        verbose_name = 'Agente'
        verbose_name_plural = 'Agentes'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (Leg. {self.legajo_numero})"


# --- Choices ---

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
    DERIVACION_DESPACHO = 'DERIVACION_DESPACHO', 'Derivación a Despacho'
    RESOLUCION_CARGADA = 'RESOLUCION_CARGADA', 'Resolución Cargada'
    DISTRIBUCION_SECTOR = 'DISTRIBUCION_SECTOR', 'Distribución a Sector'


# --- Nota y tabla intermedia ---

class Nota(models.Model):
    """
    Modelo principal que representa una nota ingresada al sistema.
    Una nota nunca se borra físicamente, solo se anula con motivo.
    numero_nota se genera automáticamente si tiene_numero_formal=False.
    """
    numero_nota = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name='Número de Nota',
        help_text='Número completo de la nota: {sector.numero}-{numero}-{año} o {sector.numero}-I{secuencia}-{año}'
    )
    tiene_numero_formal = models.BooleanField(
        default=False,
        verbose_name='Tiene Número Formal',
        help_text='True si el número lo trajo la nota física (formato completo desde formulario)'
    )
    fecha_ingreso = models.DateTimeField(
        verbose_name='Fecha de Ingreso',
        help_text='Fecha y hora en que la nota ingresó al sistema'
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
    sector_origen = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_origen',
        verbose_name='Sector de Origen',
        help_text='Sector interno de origen de la nota'
    )
    emisor_externo = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='Emisor externo',
        help_text='Entidad externa que emite la nota'
    )
    area_origen = models.CharField(
        max_length=100,
        verbose_name='Área de Origen',
        help_text='Área o departamento de origen de la nota'
    )
    tema = models.CharField(
        max_length=100,
        verbose_name='Tema',
        help_text='Tema o asunto principal de la nota (máximo 100 caracteres)'
    )
    tarea_asignada = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Tarea Asignada',
        help_text='Acción concreta que debe ejecutar el responsable'
    )
    descripcion = models.TextField(
        blank=True,
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
    genera_resolucion = models.BooleanField(
        default=False,
        verbose_name='Genera Resolución',
        help_text='Indica si esta nota genera una resolución formal'
    )
    numero_resolucion = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Número de Resolución'
    )
    fecha_resolucion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resolución'
    )
    agentes = models.ManyToManyField(
        Agente,
        through='NotaAgente',
        related_name='notas',
        blank=True,
        verbose_name='Agentes',
        help_text='Agentes asociados a esta nota'
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
        return f"{self.numero_nota or '(sin número)'} - {self.tema}"

    def save(self, *args, **kwargs):
        """
        Genera numero_nota automáticamente si tiene_numero_formal=False.
        Usa select_for_update() para evitar duplicados en concurrencia.
        """
        if not self.numero_nota:
            if self.tiene_numero_formal:
                # Si tiene número formal, debe venir completo desde el formulario
                # No generamos nada aquí, se espera que venga en el payload
                pass
            else:
                # Generar número interno automáticamente
                self.numero_nota = self._generar_numero_interno()
        super().save(*args, **kwargs)

    def _generar_numero_interno(self):
        """
        Genera número interno automáticamente según las reglas:
        - Si tiene sector_origen: {sector.numero}-I{contador+1:03d}-{año}
        - Si NO tiene sector_origen: asignar Mesa de Entradas automáticamente
        - Usa select_for_update() para evitar duplicados en concurrencia.
        """
        from django.db import transaction
        
        año = timezone.now().year
        sector = self.sector_origen
        
        # Si no tiene sector_origen, asignar Mesa de Entradas automáticamente
        if not sector:
            try:
                sector = Sector.objects.get(nombre__icontains='Mesa de Entradas', activo=True)
                self.sector_origen = sector
            except Sector.DoesNotExist:
                # Si no existe Mesa de Entradas, usar INT
                prefix = 'INT'
                sector = None
        
        if sector:
            prefix = str(sector.numero)
        else:
            prefix = 'INT'
        
        with transaction.atomic():
            # Buscar última nota del mismo sector/año con formato interno
            last = Nota.objects.filter(
                numero_nota__startswith=f"{prefix}-I",
                numero_nota__endswith=f"-{año}"
            ).select_for_update().order_by('-numero_nota').first()
            
            if last:
                # Extraer secuencia del formato {prefix}-I{seq:03d}-{año}
                parts = last.numero_nota.split('-')
                if len(parts) == 3 and parts[1].startswith('I'):
                    try:
                        seq = int(parts[1][1:]) + 1
                    except ValueError:
                        seq = 1
                else:
                    seq = 1
            else:
                seq = 1
        
        return f"{prefix}-I{seq:03d}-{año}"

    def esta_atrasada(self):
        """Verifica si la nota está atrasada respecto a su fecha límite."""
        if self.fecha_limite and self.estado not in [
            EstadoChoices.RESUELTA,
            EstadoChoices.ARCHIVADA,
            EstadoChoices.ANULADA
        ]:
            return timezone.now().date() > self.fecha_limite
        return False


class NotaAgente(models.Model):
    """Tabla intermedia entre Nota y Agente (ManyToMany con observación)."""
    nota = models.ForeignKey(
        Nota,
        on_delete=models.CASCADE,
        related_name='nota_agente_set',
        verbose_name='Nota'
    )
    agente = models.ForeignKey(
        Agente,
        on_delete=models.CASCADE,
        related_name='nota_agente_set',
        verbose_name='Agente'
    )
    observacion = models.TextField(null=True, blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Nota-Agente'
        verbose_name_plural = 'Notas-Agentes'
        unique_together = [['nota', 'agente']]

    def __str__(self):
        return f"{self.nota.numero_nota} - {self.agente}"


# --- Historial (inmutable) ---

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
        max_length=25,
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


# --- Adjuntos ---

class TipoAdjuntoChoices(models.TextChoices):
    """Tipos de adjunto asociado a una nota."""
    DOCUMENTO_ORIGINAL = 'DOCUMENTO_ORIGINAL', 'Documento Original'
    BORRADOR_RESOLUCION = 'BORRADOR_RESOLUCION', 'Borrador Resolución'
    RESOLUCION_FINAL = 'RESOLUCION_FINAL', 'Resolución Final'
    NOTA_ESCANEADA = 'NOTA_ESCANEADA', 'Nota Escaneada'
    OTRO = 'OTRO', 'Otro'


class Adjunto(models.Model):
    """Archivo adjunto asociado a una nota."""
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
    tipo_adjunto = models.CharField(
        max_length=25,
        choices=TipoAdjuntoChoices.choices,
        default=TipoAdjuntoChoices.OTRO,
        verbose_name='Tipo de Adjunto'
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


# --- Legajo y distribución ---

class TipoDocumentoLegajoChoices(models.TextChoices):
    """Tipos de documento en el legajo del agente."""
    NOTA_ESCANEADA = 'NOTA_ESCANEADA', 'Nota Escaneada'
    RESOLUCION = 'RESOLUCION', 'Resolución'
    ADJUNTO = 'ADJUNTO', 'Adjunto'
    OTRO = 'OTRO', 'Otro'


class LegajoDocumento(models.Model):
    """
    Documento vinculado al legajo personal del agente en el servidor de RRHH.
    Estructura de carpetas: /legajos/{legajo_numero}/{año}/
    """
    agente = models.ForeignKey(
        Agente,
        on_delete=models.CASCADE,
        related_name='documentos_legajo',
        verbose_name='Agente'
    )
    nota = models.ForeignKey(
        Nota,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_legajo',
        verbose_name='Nota'
    )
    nombre_archivo = models.CharField(max_length=255, verbose_name='Nombre del archivo')
    ruta_servidor = models.CharField(
        max_length=500,
        verbose_name='Ruta en servidor',
        help_text='Ruta donde se almacena en el servidor de RRHH'
    )
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumentoLegajoChoices.choices,
        verbose_name='Tipo de documento'
    )
    fecha_carga = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de carga'
    )
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_legajo_cargados',
        verbose_name='Cargado por'
    )

    class Meta:
        verbose_name = 'Documento de Legajo'
        verbose_name_plural = 'Documentos de Legajo'
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"{self.agente} - {self.nombre_archivo}"


class MedioDistribucionChoices(models.TextChoices):
    """Medio de envío de la resolución."""
    EMAIL = 'EMAIL', 'Email'
    PAPEL = 'PAPEL', 'Papel'
    SISTEMA = 'SISTEMA', 'Sistema'


class DistribucionResolucion(models.Model):
    """Registro de envío de copias de resolución a otros sectores."""
    nota = models.ForeignKey(
        Nota,
        on_delete=models.CASCADE,
        related_name='distribuciones_resolucion',
        verbose_name='Nota'
    )
    sector_destino = models.ForeignKey(
        Sector,
        on_delete=models.CASCADE,
        related_name='distribuciones_recibidas',
        verbose_name='Sector destino'
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de envío'
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='distribuciones_enviadas',
        verbose_name='Enviado por'
    )
    medio = models.CharField(
        max_length=20,
        choices=MedioDistribucionChoices.choices,
        verbose_name='Medio'
    )
    observaciones = models.TextField(null=True, blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Distribución de Resolución'
        verbose_name_plural = 'Distribuciones de Resolución'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"{self.nota.numero_nota} → {self.sector_destino}"
