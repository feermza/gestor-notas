from rest_framework import serializers
from django.utils import timezone
from .models import Nota, HistorialNota, Adjunto, Sector, EstadoChoices


class SectorSerializer(serializers.ModelSerializer):
    """Serializer para listado de sectores (dropdown)."""
    class Meta:
        model = Sector
        fields = ['id', 'nombre', 'numero']


class NotaListSerializer(serializers.ModelSerializer):
    """Serializer para listado de notas con campos esenciales."""
    responsable = serializers.SerializerMethodField()
    atrasada = serializers.SerializerMethodField()
    
    class Meta:
        model = Nota
        fields = [
            'id',
            'numero_nota',
            'tema',
            'estado',
            'prioridad',
            'responsable',
            'fecha_limite',
            'fecha_ingreso',
            'atrasada'
        ]
    
    def get_responsable(self, obj):
        """Retorna el nombre completo del responsable."""
        if obj.responsable:
            return {'id': obj.responsable.id, 'nombre_completo': obj.responsable.nombre_completo}
        return None
    
    def get_atrasada(self, obj):
        """Calcula si la nota está atrasada."""
        if obj.fecha_limite and obj.estado not in [
            EstadoChoices.ARCHIVADA,
            EstadoChoices.ANULADA
        ]:
            return timezone.now().date() > obj.fecha_limite
        return False

class NotaCreateSerializer(serializers.Serializer):
    """
    Serializer simple (no ModelSerializer) para crear notas.
    Campos exactos que envía el frontend.
    """
    sector_origen_id = serializers.IntegerField(required=True)
    responsable_id = serializers.IntegerField(required=False, allow_null=True)
    tema = serializers.CharField(required=True, max_length=100)
    tarea_asignada = serializers.CharField(required=False, allow_blank=True, max_length=200)
    prioridad = serializers.CharField(required=False, default='MEDIA')
    numero_nota_externo = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    tiene_numero_formal = serializers.BooleanField(required=False, default=False)
    fecha_ingreso = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        from usuarios.models import Usuario

        sector_origen_id = validated_data['sector_origen_id']
        responsable_id = validated_data.get('responsable_id')
        numero_externo = (validated_data.get('numero_nota_externo') or '').strip()
        sector = Sector.objects.get(id=sector_origen_id)
        request = self.context.get('request')

        # Si viene responsable_id: asignar responsable y estado ASIGNADA; si no, INGRESADA sin responsable.
        if responsable_id is not None:
            responsable = Usuario.objects.get(id=responsable_id)
            estado_inicial = EstadoChoices.ASIGNADA
        else:
            responsable = None
            estado_inicial = EstadoChoices.INGRESADA

        # Si numero_nota_externo está vacío o None: tiene_numero_formal=False y NO asignar numero_nota;
        # Nota.save() generará el número automáticamente.
        numero_nota = ''
        tiene_numero_formal = bool(numero_externo)
        if tiene_numero_formal:
            año = timezone.now().year
            numero_nota = f"{sector.numero}-{numero_externo}-{año}"

        fecha_ingreso = validated_data.get('fecha_ingreso') or timezone.now()

        nota = Nota.objects.create(
            sector_origen=sector,
            responsable=responsable,
            creado_por=request.user if request and request.user.is_authenticated else None,
            remitente='',
            area_origen='',
            estado=estado_inicial,
            tema=validated_data['tema'],
            tarea_asignada=validated_data.get('tarea_asignada', '') or '',
            prioridad=validated_data.get('prioridad', 'MEDIA'),
            tiene_numero_formal=tiene_numero_formal,
            fecha_ingreso=fecha_ingreso,
            numero_nota=numero_nota,
        )
        return nota


class NotaDetalleSerializer(serializers.ModelSerializer):
    """Serializer para detalle completo de una nota."""
    responsable = serializers.SerializerMethodField()
    creado_por = serializers.SerializerMethodField()
    historial = serializers.SerializerMethodField()
    adjuntos = serializers.SerializerMethodField()
    atrasada = serializers.SerializerMethodField()
    sector_origen_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, source='sector_origen')
    responsable_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, source='responsable')
    
    class Meta:
        model = Nota
        fields = [
            'id',
            'numero_nota',
            'tiene_numero_formal',
            'fecha_ingreso',
            'fecha_limite',
            'remitente',
            'sector_origen',
            'sector_origen_id',
            'emisor_externo',
            'area_origen',
            'tema',
            'tarea_asignada',
            'descripcion',
            'prioridad',
            'estado',
            'canal_ingreso',
            'responsable',
            'responsable_id',
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
            'numero_nota',
            'fecha_creacion',
            'ultima_modificacion',
            'creado_por'
        ]
    
    def get_responsable(self, obj):
        
        if obj.responsable:
            return {'id': obj.responsable.id, 'nombre_completo': obj.responsable.nombre_completo}
        return None
    
    def get_creado_por(self, obj):
        """Retorna el nombre completo del usuario que creó la nota."""
        if obj.creado_por:
            return obj.creado_por.nombre_completo
        return None
    
    
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
        
        # Estados que requieren motivo obligatorio (solo EN_ESPERA en el flujo actual)
        estados_con_motivo = [EstadoChoices.EN_ESPERA]
        
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
        read_only_fields = ['id', 'nota', 'usuario', 'fecha_hora', 'tipo_evento', 
                    'estado_anterior', 'estado_nuevo', 'responsable_anterior',
                    'responsable_nuevo', 'descripcion_cambio', 'campos_modificados']


class AdjuntoSerializer(serializers.ModelSerializer):
    """Serializer para adjuntos de notas."""
    nota = serializers.PrimaryKeyRelatedField(queryset=Nota.objects.all(), required=True)
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

    def create(self, validated_data):
        """Rellena ruta_almacenamiento, tipo_mime y tamaño_bytes desde el archivo si existe."""
        archivo = validated_data.pop('archivo', None)
        nombre = validated_data.get('nombre_archivo', '') or 'sin_nombre'
        validated_data['ruta_almacenamiento'] = nombre[:500]
        validated_data['tipo_mime'] = 'application/octet-stream'
        validated_data['tamaño_bytes'] = 0
        if archivo:
            validated_data['tamaño_bytes'] = getattr(archivo, 'size', 0) or 0
            ct = getattr(archivo, 'content_type', None)
            if ct:
                validated_data['tipo_mime'] = ct[:100]
        return super().create(validated_data)
