"""
Vistas de autenticación y perfil de usuario.
Usa sesiones Django (no JWT).
El login se realiza con legajo en lugar de username.
"""
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Usuario
from .permissions import EstaAutenticado


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
def usuarios_list_view(request):
    """
    Vista de listado de usuarios: GET /api/usuarios/
    Retorna lista de usuarios activos (para dropdowns).
    
    Query params:
        activos=true: filtra solo usuarios activos
    """
    queryset = Usuario.objects.all()
    
    # Filtrar por activos si se solicita
    activos = request.query_params.get('activos', '').lower() == 'true'
    if activos:
        queryset = queryset.filter(is_active=True)
    
    usuarios_data = [_datos_usuario(u) for u in queryset]
    return Response(usuarios_data, status=status.HTTP_200_OK)
