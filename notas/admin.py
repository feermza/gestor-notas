from django.contrib import admin
from django.utils.html import format_html
from .models import Nota, HistorialNota, Adjunto


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    """Administración del modelo Nota."""
    
    # Campos a mostrar en el listado
    list_display = [
        'numero_nota', 
        'tema', 
        'estado', 
        'prioridad', 
        'responsable', 
        'fecha_limite', 
        'fecha_ingreso',
        'get_area_origen_display'
    ]
    list_display_links = ['numero_nota', 'tema']
    
    # Campos editables desde el listado
    list_editable = ['estado', 'responsable']
    
    # Filtros laterales
    list_filter = ['estado', 'prioridad', 'area_origen', 'canal_ingreso', 'anulada', 'fecha_ingreso']
    
    # Campos de búsqueda
    search_fields = ['numero_nota', 'tema', 'remitente', 'descripcion', 'area_origen']
    
    # Ordenamiento por defecto
    ordering = ['-fecha_ingreso']
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_nota', 'fecha_ingreso', 'fecha_limite')
        }),
        ('Contenido', {
            'fields': ('remitente', 'area_origen', 'tema', 'descripcion')
        }),
        ('Estado y Asignación', {
            'fields': ('estado', 'prioridad', 'responsable', 'canal_ingreso')
        }),
        ('Control', {
            'fields': ('anulada', 'motivo_anulacion', 'creado_por'),
            'classes': ('collapse',)
        }),
    )
    
    # Campos de solo lectura
    readonly_fields = ['numero_nota', 'fecha_creacion', 'ultima_modificacion', 'creado_por']
    
    # Autocompletar responsable
    autocomplete_fields = ['responsable', 'creado_por']
    
    def get_area_origen_display(self, obj):
        """Muestra el área de origen."""
        return obj.area_origen
    get_area_origen_display.short_description = 'Área de Origen'
    get_area_origen_display.admin_order_field = 'area_origen'
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('responsable', 'creado_por')


@admin.register(HistorialNota)
class HistorialNotaAdmin(admin.ModelAdmin):
    """Administración del modelo HistorialNota (solo lectura)."""
    
    # Campos a mostrar en el listado
    list_display = [
        'nota', 
        'usuario', 
        'fecha_hora', 
        'tipo_evento', 
        'estado_anterior', 
        'estado_nuevo'
    ]
    list_display_links = ['nota']
    
    # Filtros laterales
    list_filter = ['tipo_evento', 'fecha_hora', 'estado_anterior', 'estado_nuevo']
    
    # Campos de búsqueda
    search_fields = ['nota__numero_nota', 'nota__tema', 'usuario__username', 'usuario__email']
    
    # Ordenamiento por defecto
    ordering = ['-fecha_hora']
    
    # Campos en el formulario de edición (todos readonly)
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
    
    # Todos los campos son de solo lectura
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
        'campos_modificados'
    ]
    
    # Deshabilitar acciones de eliminación y creación
    def has_add_permission(self, request):
        """No permite agregar registros manualmente."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permite eliminar registros del historial."""
        return False
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('nota', 'usuario', 'responsable_anterior', 'responsable_nuevo')


@admin.register(Adjunto)
class AdjuntoAdmin(admin.ModelAdmin):
    """Administración del modelo Adjunto."""
    
    # Campos a mostrar en el listado
    list_display = [
        'nota', 
        'nombre_archivo', 
        'subido_por', 
        'fecha_subida',
        'get_tamaño_formateado',
        'tipo_mime'
    ]
    list_display_links = ['nota', 'nombre_archivo']
    
    # Filtros laterales
    list_filter = ['fecha_subida', 'tipo_mime']
    
    # Campos de búsqueda
    search_fields = ['nota__numero_nota', 'nota__tema', 'nombre_archivo', 'subido_por__username']
    
    # Ordenamiento por defecto
    ordering = ['-fecha_subida']
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información Principal', {
            'fields': ('nota', 'nombre_archivo', 'subido_por', 'fecha_subida')
        }),
        ('Detalles del Archivo', {
            'fields': ('ruta_almacenamiento', 'tipo_mime', 'tamaño_bytes'),
            'classes': ('collapse',)
        }),
    )
    
    # Campos de solo lectura
    readonly_fields = ['fecha_subida']
    
    # Autocompletar
    autocomplete_fields = ['nota', 'subido_por']
    
    def get_tamaño_formateado(self, obj):
        """Muestra el tamaño del archivo formateado."""
        return obj.tamaño_formateado()
    get_tamaño_formateado.short_description = 'Tamaño'
    get_tamaño_formateado.admin_order_field = 'tamaño_bytes'
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('nota', 'subido_por')
