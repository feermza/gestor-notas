"""
Vistas de autenticación y perfil de usuario.
Usa sesiones Django (no JWT).
El login se realiza con legajo en lugar de username.
"""
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Usuario
from .permissions import EstaAutenticado, IsAdministrador
from .serializers import UsuarioSerializer


def _datos_usuario(usuario):
    """Construye el diccionario de datos del usuario para las respuestas."""
    return {
        'id': usuario.id,
        'legajo': usuario.legajo,
        'apellido': usuario.apellido,
        'nombres': usuario.nombres,
        'nombre_completo': usuario.nombre_completo,
        'email': usuario.email,
        'rol': usuario.rol,
        'rol_display': usuario.get_rol_display(),
        'activo': usuario.is_active,  # Usar is_active directamente
    }


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Vista de login: recibe legajo y password, valida credenciales,
    crea sesión Django y retorna datos del usuario y token de sesión (session_key).
    
    Request body:
        {
            "legajo": "1234",
            "password": "..."
        }
    """
    legajo = request.data.get('legajo')
    password = request.data.get('password')

    if not legajo or not password:
        return Response(
            {'error': 'Debe enviar legajo y password.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Usar el backend personalizado para autenticar con legajo
    from django.contrib.auth import authenticate
    user = authenticate(request, legajo=legajo, password=password)

    if user is None:
        return Response(
            {'error': 'Credenciales inválidas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Usuario deshabilitado.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Crear sesión Django
    login(request, user)

    return Response({
        'usuario': _datos_usuario(user),
        'session_key': request.session.session_key,
        'mensaje': 'Sesión iniciada correctamente.',
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([EstaAutenticado])
def logout_view(request):
    """Vista de logout: destruye la sesión activa."""
    logout(request)
    return Response(
        {'mensaje': 'Sesión cerrada correctamente.'},
        status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_view(request):
    """
    Vista de perfil: GET /api/usuarios/yo/
    Retorna los datos del usuario autenticado actualmente.
    """
    return Response(_datos_usuario(request.user), status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuarios_activos_view(request):
    """
    Listado de usuarios activos para dropdowns (legajo, nombre, etc.).
    GET /api/usuarios/activos/
    """
    queryset = Usuario.objects.filter(is_active=True)
    usuarios_data = [_datos_usuario(u) for u in queryset]
    return Response(usuarios_data, status=status.HTTP_200_OK)


class UsuarioViewSet(ModelViewSet):
    """
    CRUD de usuarios. Solo ADMINISTRADOR.
    list: GET /api/usuarios/
    retrieve: GET /api/usuarios/{id}/
    create: POST /api/usuarios/
    update: PUT /api/usuarios/{id}/
    partial_update: PATCH /api/usuarios/{id}/
    activar: POST /api/usuarios/{id}/activar/
    desactivar: POST /api/usuarios/{id}/desactivar/
    destroy: no implementado (se desactiva en lugar de eliminar).
    """
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdministrador]
    queryset = Usuario.objects.all().order_by('apellido', 'nombres')
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        activos = self.request.query_params.get('activos', '').lower() == 'true'
        if activos:
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        password_inicial = f"Rrhh{instance.legajo}!"
        instance.set_password(password_inicial)
        instance.save(update_fields=['password'])

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])
        return Response({'mensaje': 'Usuario activado.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        return Response({'mensaje': 'Usuario desactivado.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='resetear_password')
    def resetear_password(self, request, pk=None):
        usuario = self.get_object()
        nueva_password = f"Rrhh{usuario.legajo}!"
        usuario.set_password(nueva_password)
        usuario.save(update_fields=['password'])
        return Response(
            {'mensaje': f'Contraseña reseteada a Rrhh{usuario.legajo}!'},
            status=status.HTTP_200_OK,
        )
