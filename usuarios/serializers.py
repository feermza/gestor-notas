"""
Serializers para el modelo Usuario.
"""
from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para datos de usuario."""
    nombre_completo = serializers.SerializerMethodField()
    rol_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'legajo',
            'apellido',
            'nombres',
            'nombre_completo',
            'email',
            'rol',
            'rol_display',
            'activo',
        ]
    
    def to_representation(self, instance):
        """Incluye activo como propiedad."""
        data = super().to_representation(instance)
        data['activo'] = instance.activo
        return data
        read_only_fields = ['id', 'nombre_completo', 'rol_display']
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo en formato 'Apellido, Nombres'."""
        return obj.nombre_completo
    
    def get_rol_display(self, obj):
        """Retorna el display del rol."""
        return obj.get_rol_display()
