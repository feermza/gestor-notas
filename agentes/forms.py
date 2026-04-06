from django import forms

from .models import Agente


class AgenteCreationForm(forms.ModelForm):
    """Alta de ficha institucional sin acceso al sistema (sin contraseña utilizable)."""

    class Meta:
        model = Agente
        fields = [
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
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_unusable_password()
        instance.is_active = False
        instance.usuario_sistema = False
        instance.rol = None
        instance.debe_cambiar_password = False
        if commit:
            instance.save()
        return instance


class AgenteChangeForm(forms.ModelForm):
    """Edición institucional y estado de agente (sin rol ni acceso desde admin)."""

    class Meta:
        model = Agente
        fields = [
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
            "agente_activo",
            "usuario_sistema",
        ]
