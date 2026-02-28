from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404



from usuarios.permissions import (
    EstaAutenticado,
    EsDirectorJefeOAdmin,
    PuedeCrearNota,
    PuedeVerTodasLasNotas,
    PuedeVerNotas,
    PuedeAnularNota,
)

from .models import Nota, HistorialNota, Adjunto, Sector, EstadoChoices, TipoEventoChoices
from .serializers import (
    NotaListSerializer,
    NotaDetalleSerializer,
    NotaCambioEstadoSerializer,
    HistorialNotaSerializer,
    AdjuntoSerializer,
    SectorSerializer,
    NotaCreateSerializer,
)
from .utils import (
    es_transicion_permitida,
    crear_registro_historial
)


class NotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notas.
    
    Acciones disponibles:
    - list: Lista todas las notas con filtros
    - create: Crea una nueva nota
    - retrieve: Obtiene el detalle de una nota
    - update/partial_update: Actualiza una nota
    - cambiar_estado: Cambia el estado de una nota (acción custom)
    - pendientes: Lista notas pendientes del usuario actual (acción custom)
    - atrasadas: Lista notas atrasadas (acción custom)
    """
    serializer_class = NotaCreateSerializer

    queryset = Nota.objects.all()

    def get_permissions(self):
        """Permisos por acción según rol."""
        if self.action in ('list', 'retrieve'):
            return [EstaAutenticado(), PuedeVerNotas()]
        if self.action == 'create':
            return [EstaAutenticado(), PuedeCrearNota()]
        if self.action in ('update', 'partial_update'):
            return [EstaAutenticado(), EsDirectorJefeOAdmin()]
        if self.action == 'cambiar_estado':
            return [EstaAutenticado()]
        if self.action == 'pendientes':
            return [EstaAutenticado()]
        if self.action == 'atrasadas':
            return [EstaAutenticado(), PuedeVerTodasLasNotas()]
        return [EstaAutenticado()]

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'create':
            return NotaCreateSerializer
        elif self.action == 'list':
            return NotaListSerializer
        return NotaDetalleSerializer
    
    def get_queryset(self):
        """
        Filtra las notas según los parámetros de consulta.
        Empleado solo ve notas donde es responsable o creador.
        Filtros: estado, responsable, prioridad, atrasadas
        """
        user = self.request.user
        queryset = Nota.objects.select_related('responsable', 'creado_por').all()

        # Restricción por rol: empleado solo ve asignadas o creadas por él
        if user.is_authenticated and hasattr(user, 'puede_ver_todas_las_notas') and not user.puede_ver_todas_las_notas():
            queryset = queryset.filter(
                Q(responsable=user) | Q(creado_por=user)
            )

        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtro por responsable
        responsable_id = self.request.query_params.get('responsable', None)
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)

        # Filtro por prioridad
        prioridad = self.request.query_params.get('prioridad', None)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)

        # Filtro por notas atrasadas
        atrasadas = self.request.query_params.get('atrasadas', None)
        if atrasadas and atrasadas.lower() == 'true':
            hoy = timezone.now().date()
            queryset = queryset.filter(
                fecha_limite__lt=hoy
            ).exclude(
                estado__in=[EstadoChoices.ARCHIVADA, EstadoChoices.ANULADA]
            )

        return queryset.order_by('-fecha_ingreso')
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva nota.
        No se modifica request.data; el serializer recibe el payload tal cual.
        numero_nota se genera en Nota.save() si no tiene número formal.
        Estado inicial INGRESADA; se crea registro en historial.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nota = serializer.save()

        if request.user.is_authenticated:
            crear_registro_historial(
                nota=nota,
                usuario=request.user,
                tipo_evento=TipoEventoChoices.CREACION,
                estado_nuevo=EstadoChoices.INGRESADA,
                descripcion_cambio='Nota creada en el sistema'
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            NotaDetalleSerializer(nota).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retorna el detalle de una nota incluyendo historial y adjuntos.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Actualiza una nota y registra los cambios en el historial.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Guardar valores anteriores para el historial
        estado_anterior = instance.estado
        responsable_anterior = instance.responsable
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Detectar cambios antes de guardar
        campos_modificados = {}
        estado_nuevo = request.data.get('estado', estado_anterior)
        responsable_nuevo_id = request.data.get('responsable', None)
        
        if estado_nuevo != estado_anterior:
            campos_modificados['estado'] = {
                'anterior': estado_anterior,
                'nuevo': estado_nuevo
            }
        
        responsable_nuevo = responsable_anterior
        if responsable_nuevo_id is not None:
            responsable_id_anterior = responsable_anterior.id if responsable_anterior else None
            if int(responsable_nuevo_id) != responsable_id_anterior:
                from usuarios.models import Usuario
                responsable_nuevo = get_object_or_404(Usuario, id=responsable_nuevo_id)
                campos_modificados['responsable'] = {
                    'anterior': str(responsable_anterior) if responsable_anterior else None,
                    'nuevo': str(responsable_nuevo)
                }
        
        # Guardar cambios
        self.perform_update(serializer)
        
        # Refrescar instancia para obtener valores actualizados
        instance.refresh_from_db()
        
        # Crear registro en historial si hay cambios
        if campos_modificados and request.user.is_authenticated:
            tipo_evento = TipoEventoChoices.ACTUALIZACION
            if 'estado' in campos_modificados:
                tipo_evento = TipoEventoChoices.CAMBIO_ESTADO
            if 'responsable' in campos_modificados:
                if responsable_anterior:
                    tipo_evento = TipoEventoChoices.REASIGNACION
                else:
                    tipo_evento = TipoEventoChoices.ASIGNACION
            
            crear_registro_historial(
                nota=instance,
                usuario=request.user,
                tipo_evento=tipo_evento,
                estado_anterior=estado_anterior if 'estado' in campos_modificados else None,
                estado_nuevo=instance.estado if 'estado' in campos_modificados else None,
                responsable_anterior=responsable_anterior if 'responsable' in campos_modificados else None,
                responsable_nuevo=instance.responsable if 'responsable' in campos_modificados else None,
                descripcion_cambio=f'Actualización de campos: {", ".join(campos_modificados.keys())}',
                campos_modificados=campos_modificados
            )
        
        return Response(NotaDetalleSerializer(instance).data)
    
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Acción custom para cambiar el estado de una nota.
        Valida las transiciones permitidas y crea registro en historial.
        """
        nota = self.get_object()
        serializer = NotaCambioEstadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        estado_actual = nota.estado
        estado_nuevo = serializer.validated_data['estado_nuevo']
        motivo = serializer.validated_data.get('motivo', '')
        responsable_nuevo_id = serializer.validated_data.get('responsable_nuevo', None)
        
        # Validar transición permitida
        if not es_transicion_permitida(estado_actual, estado_nuevo):
            return Response(
                {
                    'error': 'Transición no permitida',
                    'detalle': f'No se puede cambiar de {estado_actual} a {estado_nuevo}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar permiso para anular: solo Admin o Director
        if estado_nuevo == EstadoChoices.ANULADA:
            if not request.user.is_authenticated or not getattr(request.user, 'puede_anular_nota', lambda: False)():
                return Response(
                    {'error': 'Sin permiso', 'detalle': 'Solo Director o Administrador pueden anular notas.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Validar motivo obligatorio
        estados_con_motivo = [
            EstadoChoices.EN_ESPERA,
            EstadoChoices.DEVUELTA,
            EstadoChoices.ANULADA
        ]
        if estado_nuevo in estados_con_motivo and not motivo:
            return Response(
                {
                    'error': 'Motivo requerido',
                    'detalle': f'El motivo es obligatorio para el estado {estado_nuevo}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar responsable para ASIGNADA
        if estado_nuevo == EstadoChoices.ASIGNADA and not responsable_nuevo_id:
            return Response(
                {
                    'error': 'Responsable requerido',
                    'detalle': 'El responsable es obligatorio para asignar una nota'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar valores anteriores
        responsable_anterior = nota.responsable
        
        # Actualizar nota
        nota.estado = estado_nuevo
        
        # Actualizar responsable si corresponde
        responsable_nuevo = None
        if responsable_nuevo_id:
            from usuarios.models import Usuario
            responsable_nuevo = get_object_or_404(Usuario, id=responsable_nuevo_id)
            nota.responsable = responsable_nuevo
        
        # Manejar anulación
        if estado_nuevo == EstadoChoices.ANULADA:
            nota.anulada = True
            nota.motivo_anulacion = motivo
        
        nota.save()
        
        # Determinar tipo de evento
        tipo_evento = TipoEventoChoices.CAMBIO_ESTADO
        if estado_nuevo == EstadoChoices.ANULADA:
            tipo_evento = TipoEventoChoices.ANULACION
        elif estado_nuevo == EstadoChoices.ARCHIVADA:
            tipo_evento = TipoEventoChoices.ARCHIVADO
        elif responsable_nuevo_id and responsable_anterior:
            tipo_evento = TipoEventoChoices.REASIGNACION
        elif responsable_nuevo_id and not responsable_anterior:
            tipo_evento = TipoEventoChoices.ASIGNACION
        
        # Crear registro en historial
        if request.user.is_authenticated:
            crear_registro_historial(
                nota=nota,
                usuario=request.user,
                tipo_evento=tipo_evento,
                estado_anterior=estado_actual,
                estado_nuevo=estado_nuevo,
                responsable_anterior=responsable_anterior,
                responsable_nuevo=responsable_nuevo if responsable_nuevo_id else responsable_anterior,
                descripcion_cambio=motivo or f'Cambio de estado de {estado_actual} a {estado_nuevo}'
            )
        
        return Response(
            NotaDetalleSerializer(nota).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Lista las notas asignadas al usuario actual con estado:
        ASIGNADA, EN_PROCESO, EN_ESPERA
        """
        queryset = Nota.objects.filter(
            responsable=request.user,
            estado__in=[
                EstadoChoices.ASIGNADA,
                EstadoChoices.EN_PROCESO,
                EstadoChoices.EN_ESPERA
            ]
        ).order_by('-fecha_ingreso')
        
        serializer = NotaListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        """
        Lista las notas con fecha_limite < hoy y estado no en [ARCHIVADA, ANULADA]
        """
        hoy = timezone.now().date()
        queryset = Nota.objects.filter(
            fecha_limite__lt=hoy
        ).exclude(
            estado__in=[EstadoChoices.ARCHIVADA, EstadoChoices.ANULADA]
        ).order_by('fecha_limite')
        
        serializer = NotaListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='adjuntos')
    def adjuntos(self, request, pk=None):
        """
        Crea un adjunto para la nota (POST multipart con archivo).
        URL: POST /api/notas/{id}/adjuntos/
        """
        nota = self.get_object()
        data = request.data.copy()
        data['nota'] = nota.pk
        serializer = AdjuntoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            subido_por=request.user if request.user.is_authenticated else None
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HistorialNotaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para el historial de notas.
    Solo se ven registros de notas que el usuario puede ver.
    """
    queryset = HistorialNota.objects.all()
    serializer_class = HistorialNotaSerializer
    permission_classes = [EstaAutenticado, PuedeVerNotas]

    def get_queryset(self):
        """Filtra por nota y por visibilidad (empleado solo ve historial de sus notas)."""
        user = self.request.user
        queryset = HistorialNota.objects.select_related(
            'nota', 'usuario', 'responsable_anterior', 'responsable_nuevo'
        ).all()
        if user.is_authenticated and hasattr(user, 'puede_ver_todas_las_notas') and not user.puede_ver_todas_las_notas():
            queryset = queryset.filter(
                Q(nota__responsable=user) | Q(nota__creado_por=user)
            )
        nota_id = self.request.query_params.get('nota', None)
        if nota_id:
            queryset = queryset.filter(nota_id=nota_id)
        return queryset.order_by('-fecha_hora')


class AdjuntoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar adjuntos de notas.
    Solo se ven adjuntos de notas que el usuario puede ver.
    """
    queryset = Adjunto.objects.all()
    serializer_class = AdjuntoSerializer
    permission_classes = [EstaAutenticado, PuedeVerNotas]

    def get_queryset(self):
        """Filtra por nota y por visibilidad (empleado solo ve adjuntos de sus notas)."""
        user = self.request.user
        queryset = Adjunto.objects.select_related('nota', 'subido_por').all()
        if user.is_authenticated and hasattr(user, 'puede_ver_todas_las_notas') and not user.puede_ver_todas_las_notas():
            queryset = queryset.filter(
                Q(nota__responsable=user) | Q(nota__creado_por=user)
            )
        nota_id = self.request.query_params.get('nota', None)
        if nota_id:
            queryset = queryset.filter(nota_id=nota_id)
        return queryset.order_by('-fecha_subida')
    
    def perform_create(self, serializer):
        """
        Asigna el usuario actual al adjunto al crearlo.
        """
        # TODO: Implementar subida de archivos cuando se configure MEDIA_ROOT
        serializer.save(
            subido_por=self.request.user if self.request.user.is_authenticated else None
        )


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para sectores.
    list: devuelve todos los sectores activos ordenados por nombre.
    """
    queryset = Sector.objects.filter(activo=True).order_by('nombre')
    serializer_class = SectorSerializer
    permission_classes = [EstaAutenticado]
