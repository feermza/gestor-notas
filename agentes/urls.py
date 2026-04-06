from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgenteViewSet,
    DocumentoLegajoViewSet,
    UsuarioViewSet,
    login_view,
    logout_view,
    perfil_view,
    usuarios_activos_view,
)

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuario")
router.register(r"agentes", AgenteViewSet, basename="agente")
router.register(r"documentos-legajo", DocumentoLegajoViewSet, basename="documentolegajo")

urlpatterns = [
    path("auth/login/", login_view),
    path("auth/logout/", logout_view),
    path("usuarios/yo/", perfil_view),
    path("usuarios/activos/", usuarios_activos_view),
    path("", include(router.urls)),
]
