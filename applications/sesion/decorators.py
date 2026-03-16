# applications/sesion/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse


def sesion_requerida(view_func):
    """
    Decorador personalizado que reemplaza @login_required.
    Verifica que exista usuario_id y tipo_usuario en la sesión.
    Si no, redirige al login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id') or not request.session.get('tipo_usuario'):
            # Si es una petición AJAX/API, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.content_type == 'application/json' or \
               request.path.startswith('/chat/api/') or \
               request.path.startswith('/busqueda/') or \
               request.path.startswith('/notificaciones/api/') or \
               request.path.startswith('/amistades/'):
                return JsonResponse({'error': 'No autenticado', 'redirect': '/sesion/login/'}, status=403)
            return redirect('sesion:login')
        return view_func(request, *args, **kwargs)
    return wrapper