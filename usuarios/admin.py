from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administración personalizada del modelo Usuario."""
    
    # Campos a mostrar en el listado
    list_display = ['legajo', 'apellido', 'nombres', 'dni', 'email', 'rol', 'is_active', 'last_login']
    list_display_links = ['legajo', 'email']
    
    # Campos editables desde el listado
    list_editable = ['rol', 'is_active']
    
    # Filtros laterales
    list_filter = ['rol', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    
    # Campos de búsqueda
    search_fields = ['legajo', 'apellido', 'nombres', 'dni', 'email']
    
    # Ordenamiento
    ordering = ['apellido', 'nombres']
    
    # Configuración de campos en el formulario
    # Sobrescribir fieldsets para usar nuestros campos personalizados
    fieldsets = (
        (None, {
            'fields': ('legajo', 'password')
        }),
        ('Información Personal', {
            'fields': ('apellido', 'nombres', 'dni', 'fecha_nacimiento', 'email')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Información Adicional', {
            'fields': ('rol',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Campos al crear nuevo usuario
    add_fieldsets = (
        (None, {
            'fields': ('legajo', 'password1', 'password2'),
        }),
        ('Información Personal', {
            'fields': ('apellido', 'nombres', 'dni', 'email')
        }),
        ('Información Adicional', {
            'fields': ('rol', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related()
