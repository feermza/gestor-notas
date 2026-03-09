"""
URLs de autenticación y perfil de usuarios.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')

urlpatterns = [
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('usuarios/yo/', views.perfil_view),
    path('usuarios/activos/', views.usuarios_activos_view),
    path('', include(router.urls)),
]
