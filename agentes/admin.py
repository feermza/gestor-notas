from django.contrib import admin
from django.contrib.admin.options import ModelAdmin as DjangoModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import AgenteChangeForm, AgenteCreationForm
from .models import Agente, DocumentoLegajo

_INSTITUCIONALES = (
    "legajo",
    "apellido",
    "nombres",
    "dni",
    "fecha_nacimiento",
    "email",
    "sector",
    "cargo",
    "fecha_ingreso",
    "situacion_revista",
)


class AgenteAdmin(BaseUserAdmin):
    """Padrón institucional completo (con y sin acceso al sistema)."""

    add_form = AgenteCreationForm
    form = AgenteChangeForm

    list_display = [
        "legajo",
        "apellido",
        "nombres",
        "dni",
        "agente_activo",
        "usuario_sistema",
    ]
    list_display_links = ["legajo"]
    search_fields = ["legajo", "apellido", "nombres", "dni"]
    ordering = ["apellido", "nombres"]
    autocomplete_fields = ["sector"]
    filter_horizontal = ()

    list_filter = ["agente_activo", "usuario_sistema"]

    readonly_fields = ["usuario_sistema"]

    fieldsets = (
        (
            "Datos institucionales",
            {"fields": _INSTITUCIONALES},
        ),
        (
            "Estado",
            {"fields": ("agente_activo", "usuario_sistema")},
        ),
    )

    add_fieldsets = (
        (
            "Datos institucionales",
            {
                "classes": ("wide",),
                "fields": _INSTITUCIONALES,
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("sector")

    def get_urls(self):
        return DjangoModelAdmin.get_urls(self)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_unusable_password()
            obj.is_active = False
            obj.usuario_sistema = False
        super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.fieldsets


admin.site.register(Agente, AgenteAdmin)


@admin.register(DocumentoLegajo)
class DocumentoLegajoAdmin(admin.ModelAdmin):
    list_display = ["agente", "nota", "adjunto", "archivado_por", "fecha_archivo"]
    list_filter = ["fecha_archivo"]
    search_fields = [
        "agente__legajo",
        "agente__apellido",
        "agente__nombres",
        "nota__numero_nota",
    ]
    autocomplete_fields = ["agente", "nota", "adjunto", "archivado_por"]
    readonly_fields = ["fecha_archivo"]
