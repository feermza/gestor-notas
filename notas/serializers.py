from rest_framework import serializers
from django.utils import timezone
from .models import Nota, HistorialNota, Adjunto, EstadoChoices


class NotaListSerializer(serializers.ModelSerializer):
    """Serializer para listado de notas con campos esenciales."""
    responsable = serializers.StringRelatedField(read_only=True)
    atrasada = serializers.SerializerMethodField()
    
    class Meta:
        model = Nota
        fields = [
            'id',
            'numero_nota_interno',
            'numero_nota_externo',
            'tema',
            'estado',
            'prioridad',
            'responsable',
            'fecha_limite',
            'fecha_ingreso',
            'atrasada'
        ]
    
    def get_atrasada(self, obj):
        """Calcula si la nota está atrasada."""
        if obj.fecha_limite and obj.estado not in [
            EstadoChoices.ARCHIVADA,
            EstadoChoices.ANULADA
        ]:
            return timezone.now().date() > obj.fecha_limite
        return False


class NotaDetalleSerializer(serializers.ModelSerializer):
    """Serializer para detalle completo de una nota."""
    responsable = serializers.StringRelatedField(read_only=True)
    creado_por = serializers.StringRelatedField(read_only=True)
    historial = serializers.SerializerMethodField()
    adjuntos = serializers.SerializerMethodField()
    atrasada = serializers.SerializerMethodField()
    
    class Meta:
        model = Nota
        fields = [
            'id',
            'numero_nota_interno',
            'numero_nota_externo',
            'fecha_ingreso',
            'fecha_limite',
            'remitente',
            'emisor_sector',
            'emisor_externo',
            'area_origen',
            'tema',
            'descripcion',
            'prioridad',
            'estado',
            'canal_ingreso',
            'responsable',
            'creado_por',
            'fecha_creacion',
            'ultima_modificacion',
            'anulada',
            'motivo_anulacion',
            'genera_resolucion',
            'numero_resolucion',
            'fecha_resolucion',
            'historial',
            'adjuntos',
            'atrasada'
        ]
        read_only_fields = [
            'numero_nota_interno',
            'fecha_creacion',
            'ultima_modificacion',
            'creado_por'
        ]
    
    def get_historial(self, obj):
        """Retorna el historial de la nota."""
        historial = obj.historial.all().order_by('-fecha_hora')
        return HistorialNotaSerializer(historial, many=True).data
    
    def get_adjuntos(self, obj):
        """Retorna los adjuntos de la nota."""
        adjuntos = obj.adjuntos.all().order_by('-fecha_subida')
        return AdjuntoSerializer(adjuntos, many=True).data
    
    def get_atrasada(self, obj):
        """Calcula si la nota está atrasada."""
        if obj.fecha_limite and obj.estado not in [
            EstadoChoices.ARCHIVADA,
            EstadoChoices.ANULADA
        ]:
            return timezone.now().date() > obj.fecha_limite
        return False


class NotaCambioEstadoSerializer(serializers.Serializer):
    """Serializer para cambio de estado de una nota."""
    estado_nuevo = serializers.ChoiceField(
        choices=EstadoChoices.choices,
        required=True,
        help_text='Nuevo estado al que se transiciona'
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo del cambio (obligatorio para EN_ESPERA, DEVUELTA, ANULADA)'
    )
    responsable_nuevo = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID del nuevo responsable (obligatorio para transición a ASIGNADA)'
    )
    
    def validate(self, data):
        """Valida que el motivo sea obligatorio cuando corresponde."""
        estado_nuevo = data.get('estado_nuevo')
        motivo = data.get('motivo', '')
        responsable_nuevo = data.get('responsable_nuevo')
        
        # Estados que requieren motivo obligatorio
        estados_con_motivo = [
            EstadoChoices.EN_ESPERA,
            EstadoChoices.DEVUELTA,
            EstadoChoices.ANULADA
        ]
        
        if estado_nuevo in estados_con_motivo and not motivo:
            raise serializers.ValidationError({
                'motivo': f'El motivo es obligatorio para el estado {estado_nuevo}'
            })
        
        # Transición a ASIGNADA requiere responsable
        if estado_nuevo == EstadoChoices.ASIGNADA and not responsable_nuevo:
            raise serializers.ValidationError({
                'responsable_nuevo': 'El responsable es obligatorio para asignar una nota'
            })
        
        return data


class HistorialNotaSerializer(serializers.ModelSerializer):
    """Serializer para historial de notas (solo lectura)."""
    nota = serializers.StringRelatedField(read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)
    responsable_anterior = serializers.StringRelatedField(read_only=True)
    responsable_nuevo = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = HistorialNota
        fields = [
            'id',
            'nota',
            'usuario',
            'fecha_hora',
            'tipo_evento',
            'estado_anterior',
            'estado_nuevo',
            'responsable_anterior',
            'responsable_nuevo',
            'descripcion_cambio',
            'campos_modificados'
        ]
        read_only_fields = '__all__'


class AdjuntoSerializer(serializers.ModelSerializer):
    """Serializer para adjuntos de notas."""
    nota = serializers.StringRelatedField(read_only=True)
    subido_por = serializers.StringRelatedField(read_only=True)
    archivo = serializers.FileField(write_only=True, required=False)
    tamaño_formateado = serializers.SerializerMethodField()
    
    class Meta:
        model = Adjunto
        fields = [
            'id',
            'nota',
            'nombre_archivo',
            'tipo_adjunto',
            'ruta_almacenamiento',
            'tipo_mime',
            'tamaño_bytes',
            'subido_por',
            'fecha_subida',
            'archivo',
            'tamaño_formateado'
        ]
        read_only_fields = [
            'ruta_almacenamiento',
            'tipo_mime',
            'tamaño_bytes',
            'fecha_subida',
            'subido_por'
        ]
    
    def get_tamaño_formateado(self, obj):
        """Retorna el tamaño formateado del archivo."""
        return obj.tamaño_formateado()
