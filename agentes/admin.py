from django.contrib import admin

from .models import DocumentoLegajo


@admin.register(DocumentoLegajo)
class DocumentoLegajoAdmin(admin.ModelAdmin):
    list_display = ['agente', 'nota', 'adjunto', 'archivado_por', 'fecha_archivo']
    list_filter = ['fecha_archivo']
    search_fields = [
        'agente__legajo_numero',
        'agente__apellido',
        'agente__nombre',
        'nota__numero_nota',
    ]
    autocomplete_fields = ['agente', 'nota', 'adjunto', 'archivado_por']
    readonly_fields = ['fecha_archivo']
