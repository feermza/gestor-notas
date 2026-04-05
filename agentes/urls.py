from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgenteViewSet, DocumentoLegajoViewSet

router = DefaultRouter()
router.register(r'agentes', AgenteViewSet, basename='agente')
router.register(r'documentos-legajo', DocumentoLegajoViewSet, basename='documentolegajo')

urlpatterns = [
    path('', include(router.urls)),
]
