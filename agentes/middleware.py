"""
Bloquea el uso de la API (excepto logout y cambio de contraseña) si el usuario
debe cambiar la contraseña obligatoria tras activación de acceso.
"""

from django.http import JsonResponse


def _path_allowed(path: str) -> bool:
    p = path.rstrip("/") or "/"
    return p.endswith("/api/auth/logout") or p.endswith("/api/agentes/cambiar_password")


class DebeCambiarPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if request.method == "OPTIONS":
            return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        if not getattr(user, "debe_cambiar_password", False):
            return self.get_response(request)

        if _path_allowed(request.path):
            return self.get_response(request)

        return JsonResponse(
            {
                "debe_cambiar_password": True,
                "mensaje": "Debés cambiar tu contraseña antes de continuar.",
                "redirect": "/api/agentes/cambiar_password/",
            },
            status=403,
            json_dumps_params={"ensure_ascii": False},
        )
