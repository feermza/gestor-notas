"""
URLs de autenticación y perfil de usuarios.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('usuarios/yo/', views.perfil_view),
    path('usuarios/', views.usuarios_list_view),
]
