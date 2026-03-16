# applications/sesion/middleware.py


class NoCacheMiddleware:
    """
    Agrega headers de no-caché a todas las respuestas de páginas protegidas.
    Esto evita que el navegador muestre páginas anteriores con el botón atrás
    después de cerrar sesión.
    """
    
    RUTAS_PROTEGIDAS = [
        '/sesion/home/',
        '/sesion/amigos/',
        '/perfil/',
        '/chat/',
        '/notificaciones/',
        '/publicaciones/',
        '/amistades/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Aplicar no-caché si la ruta es protegida
        if any(request.path.startswith(ruta) for ruta in self.RUTAS_PROTEGIDAS):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response