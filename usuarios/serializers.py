"""
Serializers para el modelo Usuario.
"""
from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para listado, detalle y CRUD de usuarios (solo ADMIN)."""
    nombre_completo = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = Usuario
        fields = [
            'id',
            'legajo',
            'apellido',
            'nombres',
            'nombre_completo',
            'dni',
            'email',
            'rol',
            'activo',
            'password',
        ]
        read_only_fields = ['id', 'nombre_completo']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['activo'] = instance.is_active
        data['nombre_completo'] = instance.nombre_completo
        return data

    def create(self, validated_data):
        validated_data.pop('password', None)  # No se recibe; el ViewSet asigna contraseña inicial
        activo = validated_data.pop('activo', True)
        usuario = Usuario.objects.create(**validated_data, is_active=activo)
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if 'activo' in validated_data:
            instance.is_active = validated_data.pop('activo')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
