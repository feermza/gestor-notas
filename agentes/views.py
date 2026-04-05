from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from notas.models import Agente
from usuarios.permissions import EstaAutenticado

from .models import DocumentoLegajo
from .serializers import AgenteSerializer, DocumentoLegajoSerializer


class AgenteViewSet(viewsets.ReadOnlyModelViewSet):
    """Listado y detalle de agentes activos (modelo canónico en notas)."""

    queryset = Agente.objects.filter(activo=True)
    serializer_class = AgenteSerializer
    permission_classes = [EstaAutenticado]
    filter_backends = [SearchFilter]
    search_fields = ['legajo_numero', 'apellido', 'nombre', 'dni']

    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        agente = self.get_object()
        documentos = DocumentoLegajo.objects.filter(agente=agente).select_related(
            'nota', 'adjunto', 'archivado_por'
        )
        serializer = DocumentoLegajoSerializer(
            documentos, many=True, context={'request': request}
        )
        return Response(serializer.data)


class DocumentoLegajoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoLegajo.objects.all().select_related(
        'agente', 'nota', 'adjunto', 'archivado_por'
    )
    serializer_class = DocumentoLegajoSerializer
    permission_classes = [EstaAutenticado]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):
        serializer.save(archivado_por=self.request.user)
