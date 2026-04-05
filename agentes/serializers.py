from rest_framework import serializers

from notas.models import Adjunto, Agente, Nota
from .models import DocumentoLegajo


class AgenteSerializer(serializers.ModelSerializer):
    """Expone el agente canónico (notas.Agente) con nombres de API legajo / nombres."""

    legajo = serializers.CharField(source='legajo_numero', read_only=True)
    nombres = serializers.CharField(source='nombre', read_only=True)
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Agente
        fields = [
            'id',
            'legajo',
            'apellido',
            'nombres',
            'nombre_completo',
            'dni',
            'activo',
        ]


class DocumentoLegajoSerializer(serializers.ModelSerializer):
    agente = AgenteSerializer(read_only=True)
    agente_id = serializers.PrimaryKeyRelatedField(
        queryset=Agente.objects.all(),
        source='agente',
        write_only=True,
    )
    nota = serializers.PrimaryKeyRelatedField(read_only=True)
    nota_id = serializers.PrimaryKeyRelatedField(
        queryset=Nota.objects.all(),
        source='nota',
        write_only=True,
    )
    adjunto = serializers.PrimaryKeyRelatedField(read_only=True)
    adjunto_id = serializers.PrimaryKeyRelatedField(
        queryset=Adjunto.objects.all(),
        source='adjunto',
        write_only=True,
    )
    nota_numero = serializers.CharField(source='nota.numero_nota', read_only=True)
    nota_tema = serializers.CharField(source='nota.tema', read_only=True)
    adjunto_nombre = serializers.CharField(
        source='adjunto.nombre_archivo', read_only=True
    )
    adjunto_url = serializers.SerializerMethodField()
    archivado_por_nombre = serializers.CharField(
        source='archivado_por.nombre_completo', read_only=True
    )

    class Meta:
        model = DocumentoLegajo
        fields = [
            'id',
            'agente',
            'agente_id',
            'nota',
            'nota_id',
            'nota_numero',
            'nota_tema',
            'adjunto',
            'adjunto_id',
            'adjunto_nombre',
            'adjunto_url',
            'archivado_por_nombre',
            'fecha_archivo',
        ]
        read_only_fields = ['fecha_archivo']

    def get_adjunto_url(self, obj):
        """Misma convención que notas.serializers.AdjuntoSerializer.get_url."""
        adj = obj.adjunto
        if not adj or not adj.ruta_almacenamiento:
            return None
        return f"http://localhost:8000/media/{adj.ruta_almacenamiento}"

    def validate(self, attrs):
        nota = attrs.get('nota')
        adjunto = attrs.get('adjunto')
        if self.instance is not None:
            nota = nota if 'nota' in attrs else self.instance.nota
            adjunto = adjunto if 'adjunto' in attrs else self.instance.adjunto
        if nota and adjunto and adjunto.nota_id != nota.pk:
            raise serializers.ValidationError(
                {'adjunto_id': 'El adjunto debe pertenecer a la nota indicada.'}
            )
        return attrs
