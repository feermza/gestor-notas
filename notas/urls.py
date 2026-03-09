from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotaViewSet,
    HistorialNotaViewSet,
    AdjuntoViewSet,
    SectorViewSet,
    reporte_notas_por_sector,
    reporte_notas_por_operador,
    auditoria_list,
)

# Crear router de DRF
router = DefaultRouter()
router.register(r'notas', NotaViewSet, basename='nota')
router.register(r'historial', HistorialNotaViewSet, basename='historial')
router.register(r'adjuntos', AdjuntoViewSet, basename='adjunto')
router.register(r'sectores', SectorViewSet, basename='sector')

urlpatterns = [
    path('', include(router.urls)),
    path('reportes/notas-por-sector/', reporte_notas_por_sector),
    path('reportes/notas-por-operador/', reporte_notas_por_operador),
    path('auditoria/', auditoria_list),
]
