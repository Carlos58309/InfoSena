# applications/sesion/middleware.py


class NoCacheMiddleware:
    """
    1. Agrega headers no-caché a TODAS las páginas protegidas.
    2. Si el usuario no tiene sesión e intenta entrar a una ruta
       protegida, lo manda al login — incluso si el navegador
       sirvió una copia en caché del HTML.
    """

    # Rutas que NO requieren sesión (públicas)
    RUTAS_PUBLICAS = [
        '/sesion/login/',
        '/sesion/logout/',
        '/sesion/verificar-sesion/',
        '/sesion/solicitar-correo/',
        '/sesion/verificar-codigo/',
        '/sesion/nueva-contrasena/',
        '/sesion/',          # index/landing
        '/registro/',
        '/static/',
        '/media/',
        '/admin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def es_ruta_publica(self, path):
        for ruta in self.RUTAS_PUBLICAS:
            if path.startswith(ruta) or path == '/':
                return True
        return False

    def tiene_sesion(self, request):
        return bool(
            request.session.get('usuario_id') and
            request.session.get('tipo_usuario')
        )

    def __call__(self, request):
        es_publica = self.es_ruta_publica(request.path)
        sesion_activa = self.tiene_sesion(request)

        # ── Bloquear rutas protegidas sin sesión ──────────────────────────
        if not es_publica and not sesion_activa:
            from django.http import JsonResponse
            from django.shortcuts import redirect

            es_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Accept', '')
                or request.content_type == 'application/json'
            )

            if es_ajax:
                return JsonResponse(
                    {'error': 'Sesión expirada', 'redirect': '/sesion/login/'},
                    status=403
                )

            return redirect('/sesion/login/')

        response = self.get_response(request)

        # ── Agregar headers no-caché a páginas protegidas ─────────────────
        if not es_publica:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response