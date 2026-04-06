"""Autenticación por legajo (AUTH_USER_MODEL = agentes.Agente)."""
from django.contrib.auth.backends import ModelBackend

from .models import Agente


class LegajoBackend(ModelBackend):
    def authenticate(self, request, legajo=None, password=None, **kwargs):
        if legajo is None or password is None:
            return None
        try:
            usuario = Agente.objects.get(legajo=legajo)
        except Agente.DoesNotExist:
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None

    def get_user(self, user_id):
        try:
            return Agente.objects.get(pk=user_id)
        except Agente.DoesNotExist:
            return None
