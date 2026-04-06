import re

from rest_framework import serializers

from notas.models import Adjunto, Nota

from .models import Agente, DocumentoLegajo, RolChoices


class AgenteDisponibleParaActivarSerializer(serializers.ModelSerializer):
    """Agentes con ficha activa y sin acceso al sistema (modal alta usuario)."""

    class Meta:
        model = Agente
        fields = ["id", "legajo", "apellido", "nombres", "dni", "email"]


class AgenteListSerializer(serializers.ModelSerializer):
    """Listado / buscador (modal activación): acceso al sistema y flags."""

    nombre_completo = serializers.ReadOnlyField()
    tiene_acceso = serializers.SerializerMethodField()

    class Meta:
        model = Agente
        fields = [
            "id",
            "legajo",
            "apellido",
            "nombres",
            "dni",
            "email",
            "rol",
            "is_active",
            "agente_activo",
            "usuario_sistema",
            "debe_cambiar_password",
            "nombre_completo",
            "tiene_acceso",
        ]

    def get_tiene_acceso(self, obj):
        return bool(obj.usuario_sistema)


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nuevo = serializers.CharField(write_only=True)
    password_nuevo_confirmacion = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Sesión no válida.")

        user = request.user
        actual = attrs["password_actual"]

        if not user.check_password(actual):
            raise serializers.ValidationError(
                {"password_actual": "La contraseña actual es incorrecta."}
            )

        p1 = attrs["password_nuevo"]
        p2 = attrs["password_nuevo_confirmacion"]
        if p1 != p2:
            raise serializers.ValidationError(
                {
                    "password_nuevo_confirmacion": "Las contraseñas nuevas no coinciden.",
                }
            )

        if p1 == actual:
            raise serializers.ValidationError(
                {
                    "password_nuevo": "La contraseña nueva debe ser diferente a la actual.",
                }
            )

        ok, msg = _validar_requisitos_password(p1)
        if not ok:
            raise serializers.ValidationError({"password_nuevo": msg})

        return attrs


def _validar_requisitos_password(password: str):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Debe incluir al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "Debe incluir al menos una letra minúscula."
    if not re.search(r"\d", password):
        return False, "Debe incluir al menos un dígito."
    return True, ""


class AgenteSerializer(serializers.ModelSerializer):
    """Listado público de agentes (legajo virtual)."""

    nombre_completo = serializers.ReadOnlyField()
    activo = serializers.BooleanField(source="activo_rrhh", read_only=True)

    class Meta:
        model = Agente
        fields = [
            "id",
            "legajo",
            "apellido",
            "nombres",
            "nombre_completo",
            "dni",
            "activo_rrhh",
            "activo",
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    """CRUD /api/usuarios/ (agentes con rol de sistema)."""

    nombre_completo = serializers.CharField(read_only=True)
    activo = serializers.BooleanField(source="is_active", required=False, default=True)
    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )

    class Meta:
        model = Agente
        fields = [
            "id",
            "legajo",
            "apellido",
            "nombres",
            "nombre_completo",
            "dni",
            "email",
            "rol",
            "activo",
            "password",
        ]
        read_only_fields = ["id", "nombre_completo"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["activo"] = instance.is_active
        data["nombre_completo"] = instance.nombre_completo
        return data

    def create(self, validated_data):
        validated_data.pop("password", None)
        if validated_data.get("rol") is None:
            validated_data["rol"] = RolChoices.OPERADOR
        validated_data.setdefault("usuario_sistema", True)
        return Agente.objects.create(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class DocumentoLegajoSerializer(serializers.ModelSerializer):
    agente = AgenteSerializer(read_only=True)
    agente_id = serializers.PrimaryKeyRelatedField(
        queryset=Agente.objects.all(),
        source="agente",
        write_only=True,
    )
    nota = serializers.PrimaryKeyRelatedField(read_only=True)
    nota_id = serializers.PrimaryKeyRelatedField(
        queryset=Nota.objects.all(),
        source="nota",
        write_only=True,
    )
    adjunto = serializers.PrimaryKeyRelatedField(read_only=True)
    adjunto_id = serializers.PrimaryKeyRelatedField(
        queryset=Adjunto.objects.all(),
        source="adjunto",
        write_only=True,
    )
    nota_numero = serializers.CharField(source="nota.numero_nota", read_only=True)
    nota_tema = serializers.CharField(source="nota.tema", read_only=True)
    adjunto_nombre = serializers.CharField(
        source="adjunto.nombre_archivo", read_only=True
    )
    adjunto_url = serializers.SerializerMethodField()
    archivado_por_nombre = serializers.CharField(
        source="archivado_por.nombre_completo", read_only=True
    )

    class Meta:
        model = DocumentoLegajo
        fields = [
            "id",
            "agente",
            "agente_id",
            "nota",
            "nota_id",
            "nota_numero",
            "nota_tema",
            "adjunto",
            "adjunto_id",
            "adjunto_nombre",
            "adjunto_url",
            "archivado_por_nombre",
            "fecha_archivo",
        ]
        read_only_fields = ["fecha_archivo"]

    def get_adjunto_url(self, obj):
        adj = obj.adjunto
        if not adj or not adj.ruta_almacenamiento:
            return None
        return f"http://localhost:8000/media/{adj.ruta_almacenamiento}"

    def validate(self, attrs):
        nota = attrs.get("nota")
        adjunto = attrs.get("adjunto")
        if self.instance is not None:
            nota = nota if "nota" in attrs else self.instance.nota
            adjunto = adjunto if "adjunto" in attrs else self.instance.adjunto
        if nota and adjunto and adjunto.nota_id != nota.pk:
            raise serializers.ValidationError(
                {"adjunto_id": "El adjunto debe pertenecer a la nota indicada."}
            )
        return attrs
