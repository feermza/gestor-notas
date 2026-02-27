from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Sector,
    Agente,
    Nota,
    NotaAgente,
    HistorialNota,
    Adjunto,
    LegajoDocumento,
    DistribucionResolucion,
)


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    """Administración del modelo Sector."""
    list_display = ['numero', 'nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['numero']


@admin.register(Agente)
class AgenteAdmin(admin.ModelAdmin):
    """Administración del modelo Agente."""
    list_display = ['legajo_numero', 'apellido', 'nombre', 'sector', 'cargo', 'activo', 'usuario']
    list_filter = ['activo', 'sector']
    search_fields = ['apellido', 'nombre', 'legajo_numero', 'cargo']
    list_editable = ['activo']
    autocomplete_fields = ['sector', 'usuario']
    ordering = ['apellido', 'nombre']


class NotaAgenteInline(admin.TabularInline):
    """Inline para gestionar agentes asociados a una nota."""
    model = NotaAgente
    extra = 0
    autocomplete_fields = ['agente']


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    """Administración del modelo Nota."""
    
    list_display = [
        'numero_nota',
        'tema',
        'estado',
        'prioridad',
        'responsable',
        'fecha_limite',
        'fecha_ingreso',
        'get_area_origen_display',
    ]
    list_display_links = ['numero_nota', 'tema']
    
    list_editable = ['estado', 'responsable']
    
    list_filter = [
        'estado',
        'prioridad',
        'area_origen',
        'canal_ingreso',
        'anulada',
        'fecha_ingreso',
        'genera_resolucion',
    ]
    
    search_fields = [
        'numero_nota',
        'tema',
        'remitente',
        'descripcion',
        'area_origen',
        'tarea_asignada',
    ]
    
    ordering = ['-fecha_ingreso']
    
    fieldsets = (
        ('Numeración', {
            'fields': ('numero_nota', 'tiene_numero_formal')
        }),
        ('Información Básica', {
            'fields': ('fecha_ingreso', 'fecha_limite')
        }),
        ('Origen y Contenido', {
            'fields': (
                'remitente',
                'sector_origen',
                'emisor_externo',
                'area_origen',
                'tema',
                'tarea_asignada',
                'descripcion',
            )
        }),
        ('Estado y Asignación', {
            'fields': ('estado', 'prioridad', 'responsable', 'canal_ingreso')
        }),
        ('Resolución', {
            'fields': (
                'genera_resolucion',
                'numero_resolucion',
                'fecha_resolucion',
            ),
            'classes': ('collapse',)
        }),
        ('Control', {
            'fields': ('anulada', 'motivo_anulacion', 'creado_por'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'numero_nota',
        'fecha_creacion',
        'ultima_modificacion',
        'creado_por',
    ]
    
    autocomplete_fields = ['sector_origen', 'responsable', 'creado_por']
    inlines = [NotaAgenteInline]
    
    def get_area_origen_display(self, obj):
        """Muestra el área de origen."""
        return obj.area_origen
    get_area_origen_display.short_description = 'Área de Origen'
    get_area_origen_display.admin_order_field = 'area_origen'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'responsable',
            'creado_por',
            'sector_origen',
        )


@admin.register(HistorialNota)
class HistorialNotaAdmin(admin.ModelAdmin):
    """Administración del modelo HistorialNota (solo lectura)."""
    
    list_display = [
        'nota',
        'usuario',
        'fecha_hora',
        'tipo_evento',
        'estado_anterior',
        'estado_nuevo',
    ]
    list_display_links = ['nota']
    
    list_filter = ['tipo_evento', 'fecha_hora', 'estado_anterior', 'estado_nuevo']
    
    search_fields = [
        'nota__numero_nota',
        'nota__tema',
        'usuario__legajo',
        'usuario__email',
    ]
    
    ordering = ['-fecha_hora']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('nota', 'usuario', 'fecha_hora', 'tipo_evento')
        }),
        ('Cambios de Estado', {
            'fields': ('estado_anterior', 'estado_nuevo')
        }),
        ('Cambios de Responsable', {
            'fields': ('responsable_anterior', 'responsable_nuevo'),
            'classes': ('collapse',)
        }),
        ('Detalles del Cambio', {
            'fields': ('descripcion_cambio', 'campos_modificados'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'nota',
        'usuario',
        'fecha_hora',
        'tipo_evento',
        'estado_anterior',
        'estado_nuevo',
        'responsable_anterior',
        'responsable_nuevo',
        'descripcion_cambio',
        'campos_modificados',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'nota',
            'usuario',
            'responsable_anterior',
            'responsable_nuevo',
        )


@admin.register(Adjunto)
class AdjuntoAdmin(admin.ModelAdmin):
    """Administración del modelo Adjunto."""
    
    list_display = [
        'nota',
        'nombre_archivo',
        'tipo_adjunto',
        'subido_por',
        'fecha_subida',
        'get_tamaño_formateado',
        'tipo_mime',
    ]
    list_display_links = ['nota', 'nombre_archivo']
    
    list_filter = ['fecha_subida', 'tipo_mime', 'tipo_adjunto']
    
    search_fields = [
        'nota__numero_nota',
        'nota__tema',
        'nombre_archivo',
        'subido_por__legajo',
    ]
    
    ordering = ['-fecha_subida']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('nota', 'nombre_archivo', 'tipo_adjunto', 'subido_por', 'fecha_subida')
        }),
        ('Detalles del Archivo', {
            'fields': ('ruta_almacenamiento', 'tipo_mime', 'tamaño_bytes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_subida']
    autocomplete_fields = ['nota', 'subido_por']
    
    def get_tamaño_formateado(self, obj):
        return obj.tamaño_formateado()
    get_tamaño_formateado.short_description = 'Tamaño'
    get_tamaño_formateado.admin_order_field = 'tamaño_bytes'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('nota', 'subido_por')


@admin.register(LegajoDocumento)
class LegajoDocumentoAdmin(admin.ModelAdmin):
    """Administración del modelo LegajoDocumento."""
    list_display = ['agente', 'nota', 'nombre_archivo', 'tipo_documento', 'fecha_carga', 'cargado_por']
    list_filter = ['tipo_documento', 'fecha_carga']
    search_fields = ['agente__apellido', 'agente__nombre', 'agente__legajo_numero', 'nombre_archivo']
    autocomplete_fields = ['agente', 'nota', 'cargado_por']
    readonly_fields = ['fecha_carga']
    ordering = ['-fecha_carga']


@admin.register(DistribucionResolucion)
class DistribucionResolucionAdmin(admin.ModelAdmin):
    """Administración del modelo DistribucionResolucion."""
    list_display = ['nota', 'sector_destino', 'medio', 'fecha_envio', 'enviado_por']
    list_filter = ['medio', 'fecha_envio']
    search_fields = ['nota__numero_nota', 'sector_destino__nombre']
    autocomplete_fields = ['nota', 'sector_destino', 'enviado_por']
    readonly_fields = ['fecha_envio']
    ordering = ['-fecha_envio']
