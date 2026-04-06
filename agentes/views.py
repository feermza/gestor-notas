from django.contrib.auth import login, logout, update_session_auth_hash
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Agente, DocumentoLegajo, RolChoices
from .permissions import EstaAutenticado, IsAdministrador
from .serializers import (
    AgenteDisponibleParaActivarSerializer,
    AgenteListSerializer,
    AgenteSerializer,
    CambiarPasswordSerializer,
    DocumentoLegajoSerializer,
    UsuarioSerializer,
)

_ROLES_ACTIVACION = {c.value for c in RolChoices}


def _datos_usuario(usuario):
    return {
        "id": usuario.id,
        "legajo": usuario.legajo,
        "apellido": usuario.apellido,
        "nombres": usuario.nombres,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email or "",
        "rol": usuario.rol,
        "rol_display": usuario.get_rol_display(),
        "activo": usuario.is_active,
        "debe_cambiar_password": getattr(usuario, "debe_cambiar_password", False),
    }


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    legajo = request.data.get("legajo")
    password = request.data.get("password")

    if not legajo or not password:
        return Response(
            {"error": "Debe enviar legajo y password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from django.contrib.auth import authenticate

    user = authenticate(request, legajo=legajo, password=password)

    if user is None:
        return Response(
            {"error": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"error": "Usuario deshabilitado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not user.usuario_sistema:
        return Response(
            {"error": "Este legajo no tiene permisos de acceso al sistema."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not user.rol:
        return Response(
            {"error": "Este legajo no tiene permisos de acceso al sistema."},
            status=status.HTTP_403_FORBIDDEN,
        )

    login(request, user)

    return Response(
        {
            "usuario": _datos_usuario(user),
            "session_key": request.session.session_key,
            "mensaje": "Sesión iniciada correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@api_view(["POST"])
@permission_classes([EstaAutenticado])
def logout_view(request):
    logout(request)
    return Response(
        {"mensaje": "Sesión cerrada correctamente."},
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil_view(request):
    return Response(_datos_usuario(request.user), status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usuarios_activos_view(request):
    queryset = Agente.objects.filter(
        usuario_sistema=True,
        is_active=True,
        rol__isnull=False,
    ).exclude(rol=RolChoices.CONSULTOR)
    return Response([_datos_usuario(u) for u in queryset], status=status.HTTP_200_OK)


class UsuarioViewSet(ModelViewSet):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdministrador]
    queryset = Agente.objects.all().order_by("apellido", "nombres")
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        activos = self.request.query_params.get("activos", "").lower() == "true"
        if activos:
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(
            debe_cambiar_password=False, usuario_sistema=True
        )
        password_inicial = f"Rrhh{instance.legajo}!"
        instance.set_password(password_inicial)
        instance.save(update_fields=["password"])

    @action(detail=True, methods=["post"], url_path="activar")
    def activar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = True
        usuario.usuario_sistema = True
        usuario.save(update_fields=["is_active", "usuario_sistema"])
        return Response({"mensaje": "Usuario activado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = False
        usuario.usuario_sistema = False
        usuario.save(update_fields=["is_active", "usuario_sistema"])
        return Response({"mensaje": "Usuario desactivado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="resetear_password")
    def resetear_password(self, request, pk=None):
        usuario = self.get_object()
        nueva_password = f"Rrhh{usuario.legajo}!"
        usuario.set_password(nueva_password)
        usuario.save(update_fields=["password"])
        return Response(
            {"mensaje": f"Contraseña reseteada a Rrhh{usuario.legajo}!"},
            status=status.HTTP_200_OK,
        )


class AgenteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Listado de agentes (filtros query) y acciones de activación/revocación de acceso.
    """

    queryset = Agente.objects.all()
    serializer_class = AgenteListSerializer
    permission_classes = [EstaAutenticado]
    filter_backends = [SearchFilter]
    search_fields = ["legajo", "apellido", "nombres", "dni"]

    def get_queryset(self):
        qs = Agente.objects.all().order_by("apellido", "nombres")
        legajo = self.request.query_params.get("legajo")
        apellido = self.request.query_params.get("apellido")
        dni = self.request.query_params.get("dni")
        if legajo:
            qs = qs.filter(legajo__icontains=legajo.strip())
        if apellido:
            qs = qs.filter(apellido__icontains=apellido.strip())
        if dni:
            qs = qs.filter(dni__icontains=dni.strip())
        return qs

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAdministrador],
        url_path="disponibles_para_activar",
    )
    def disponibles_para_activar(self, request):
        qs = Agente.objects.filter(
            agente_activo=True, usuario_sistema=False
        ).order_by("apellido", "nombres")
        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(legajo__icontains=search)
                | Q(apellido__icontains=search)
                | Q(nombres__icontains=search)
                | Q(dni__icontains=search)
            )
        data = AgenteDisponibleParaActivarSerializer(qs, many=True).data
        return Response(data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrador],
        url_path="activar_acceso",
    )
    def activar_acceso(self, request, pk=None):
        agente = self.get_object()
        if not agente.agente_activo:
            return Response(
                {
                    "error": "No se puede activar un agente dado de baja en la institución."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if agente.usuario_sistema:
            return Response(
                {"error": "El agente ya tiene acceso al sistema."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rol = request.data.get("rol")
        if rol not in _ROLES_ACTIVACION:
            return Response(
                {
                    "error": "Rol inválido. Use ADMINISTRADOR, SUPERVISOR, OPERADOR o CONSULTOR."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        password_temporal = f"Utn{agente.legajo}!"
        agente.usuario_sistema = True
        agente.rol = rol
        agente.is_active = True
        agente.debe_cambiar_password = True
        agente.set_password(password_temporal)
        agente.save()
        return Response(
            {
                "mensaje": "Acceso activado correctamente.",
                "legajo": agente.legajo,
                "nombre_completo": agente.nombre_completo,
                "rol": agente.rol,
                "password_temporal": password_temporal,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrador],
        url_path="desactivar_acceso",
    )
    def desactivar_acceso(self, request, pk=None):
        agente = self.get_object()
        if not agente.usuario_sistema:
            return Response(
                {"error": "El agente no tiene acceso activo al sistema."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        agente.usuario_sistema = False
        agente.is_active = False
        agente.rol = None
        agente.debe_cambiar_password = False
        agente.set_unusable_password()
        agente.save()
        return Response(
            {"mensaje": "Acceso al sistema revocado correctamente."},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="cambiar_password",
    )
    def cambiar_password(self, request):
        serializer = CambiarPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        nuevo = serializer.validated_data["password_nuevo"]
        user.set_password(nuevo)
        user.debe_cambiar_password = False
        user.save()
        update_session_auth_hash(request, user)
        return Response({"mensaje": "Contraseña actualizada correctamente."})

    @action(detail=True, methods=["get"])
    def documentos(self, request, pk=None):
        agente = self.get_object()
        documentos = DocumentoLegajo.objects.filter(agente=agente).select_related(
            "nota", "adjunto", "archivado_por"
        )
        serializer = DocumentoLegajoSerializer(
            documentos, many=True, context={"request": request}
        )
        return Response(serializer.data)


class DocumentoLegajoViewSet(ModelViewSet):
    queryset = DocumentoLegajo.objects.all().select_related(
        "agente", "nota", "adjunto", "archivado_por"
    )
    serializer_class = DocumentoLegajoSerializer
    permission_classes = [EstaAutenticado]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        serializer.save(archivado_por=self.request.user)
