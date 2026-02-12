from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_requerido(view_func):
    """
    Decorador para restringir acceso solo a usuarios administradores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar si hay usuario en sesión
        if 'usuario_id' not in request.session:
            messages.error(request, '❌ Debes iniciar sesión para acceder.')
            return redirect('sesion:login')
        
        # Obtener el usuario desde la sesión
        from usuarios.models import Usuario
        try:
            usuario = Usuario.objects.get(documento=request.session['usuario_id'])
            
            # Verificar si es admin
            if not usuario.es_admin:
                messages.error(request, '🚫 No tienes permisos para acceder a esta página.')
                return redirect('sesion:home')
            
            # Si es admin, permitir acceso
            return view_func(request, *args, **kwargs)
            
        except Usuario.DoesNotExist:
            messages.error(request, '❌ Usuario no encontrado.')
            return redirect('sesion:login')
    
    return wrapper