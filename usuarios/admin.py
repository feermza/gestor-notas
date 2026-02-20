from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administración personalizada del modelo Usuario."""
    
    # Campos a mostrar en el listado
    list_display = ['username', 'email', 'get_full_name', 'rol', 'is_active', 'last_login']
    list_display_links = ['username', 'email']
    
    # Campos editables desde el listado
    list_editable = ['rol']
    
    # Filtros laterales
    list_filter = ['rol', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    
    # Campos de búsqueda
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # Configuración de campos en el formulario
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('rol',)
        }),
    )
    
    # Campos al crear nuevo usuario
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'email', 'first_name', 'last_name')
        }),
    )
    
    # Métodos personalizados para mostrar información
    def get_full_name(self, obj):
        """Retorna el nombre completo del usuario."""
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Nombre Completo'
    get_full_name.admin_order_field = 'last_name'
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related()
