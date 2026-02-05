# applications/notificaciones/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notificacion
from applications.usuarios.models import Usuario

@login_required
def obtener_notificaciones(request):
    """API para obtener notificaciones no leídas (para el header)"""
    try:
        # Obtener usuario actual
        from applications.sesion.views import obtener_usuario_actual
        usuario_actual, _ = obtener_usuario_actual(request)
        
        if not usuario_actual:
            return JsonResponse({'notificaciones': [], 'count': 0})
        
        # Obtener notificaciones no leídas
        notificaciones = Notificacion.objects.filter(
            destinatario=usuario_actual,
            leida=False
        )[:10]  # Máximo 10 notificaciones
        
        data = {
            'count': notificaciones.count(),
            'notificaciones': [
                {
                    'id': n.id,
                    'tipo': n.tipo,
                    'mensaje': n.mensaje,
                    'emisor_nombre': n.emisor.nombre,
                    'emisor_foto': n.emisor.foto.url if n.emisor.foto else None,
                    'fecha': n.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                    'publicacion_id': n.publicacion.id if n.publicacion else None,
                }
                for n in notificaciones
            ]
        }
        
        return JsonResponse(data)
    except Exception as e:
        print(f"Error obteniendo notificaciones: {e}")
        return JsonResponse({'notificaciones': [], 'count': 0})


@login_required
def marcar_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    try:
        from applications.sesion.views import obtener_usuario_actual
        usuario_actual, _ = obtener_usuario_actual(request)
        
        notificacion = Notificacion.objects.get(
            id=notificacion_id,
            destinatario=usuario_actual
        )
        notificacion.marcar_como_leida()
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False})


@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas"""
    try:
        from applications.sesion.views import obtener_usuario_actual
        usuario_actual, _ = obtener_usuario_actual(request)
        
        Notificacion.objects.filter(
            destinatario=usuario_actual,
            leida=False
        ).update(leida=True)
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False})


@login_required
def lista_notificaciones(request):
    """Vista completa de todas las notificaciones"""
    from applications.sesion.views import obtener_usuario_actual
    usuario_actual, datos_usuario = obtener_usuario_actual(request)
    
    if not usuario_actual:
        return redirect('sesion:home')
    
    
    # Obtener todas las notificaciones
    notificaciones = Notificacion.objects.filter(
        destinatario=usuario_actual
    )
    
    # Marcar todas como leídas
    notificaciones.filter(leida=False).update(leida=True)
    
    context = {
        'notificaciones': notificaciones,
        'usuario': datos_usuario,
        'tipo_perfil': request.session.get('tipo_usuario'),
    }
    
    return render(request, 'notificaciones.html', context)