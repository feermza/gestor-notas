from django.conf import settings
from django.db import models


class DocumentoLegajo(models.Model):
    """
    Vincula un adjunto de una nota al legajo personal virtual del agente
    (modelo canónico en notas.Agente). Complementa LegajoDocumento (archivo en servidor RRHH).
    """

    agente = models.ForeignKey(
        'notas.Agente',
        on_delete=models.PROTECT,
        related_name='documentos_legajo_virtual',
        verbose_name='Agente',
    )
    nota = models.ForeignKey(
        'notas.Nota',
        on_delete=models.PROTECT,
        related_name='documentos_legajo_virtual',
        verbose_name='Nota',
    )
    adjunto = models.ForeignKey(
        'notas.Adjunto',
        on_delete=models.PROTECT,
        related_name='documentos_legajo_virtual',
        verbose_name='Adjunto',
    )
    archivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documentos_legajo_archivados',
        verbose_name='Archivado por',
    )
    fecha_archivo = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de archivo',
    )

    class Meta:
        ordering = ['-fecha_archivo']
        verbose_name = 'Documento de Legajo (virtual)'
        verbose_name_plural = 'Documentos de Legajo (virtual)'

    def __str__(self):
        return f"{self.agente} - {self.nota.numero_nota}"
