from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotaViewSet, HistorialNotaViewSet, AdjuntoViewSet, SectorViewSet

# Crear router de DRF
router = DefaultRouter()
router.register(r'notas', NotaViewSet, basename='nota')
router.register(r'historial', HistorialNotaViewSet, basename='historial')
router.register(r'adjuntos', AdjuntoViewSet, basename='adjunto')
router.register(r'sectores', SectorViewSet, basename='sector')

urlpatterns = [
    path('', include(router.urls)),
]
