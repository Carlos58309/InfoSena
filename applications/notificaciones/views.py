# applications/notificaciones/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notificacion
from applications.usuarios.models import Usuario
from applications.sesion.decorators import sesion_requerida

def _get_usuario(request):
    """Helper reutilizable para obtener el usuario actual."""
    try:
        from applications.sesion.views import obtener_usuario_actual
        return obtener_usuario_actual(request)
    except Exception:
        return None, None


# ─────────────────────────────────────────────────────────────
#  API: OBTENER NOTIFICACIONES (header)
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def obtener_notificaciones(request):
    try:
        usuario_actual, _ = _get_usuario(request)
        if not usuario_actual:
            return JsonResponse({'notificaciones': [], 'count': 0})

        notificaciones = Notificacion.objects.filter(
            destinatario=usuario_actual,
            leida=False
        ).select_related('emisor').order_by('-fecha_creacion')[:10]

        data = {
            'count': notificaciones.count(),
            'notificaciones': [
                {
                    'id': n.id,
                    'tipo': n.tipo,
                    'mensaje': n.mensaje,
                    'emisor_nombre': n.emisor.nombre,
                    'emisor_id': n.emisor.id,
                    'emisor_foto': n.emisor.foto.url if n.emisor.foto else None,
                    'fecha': n.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                    'publicacion_id': n.publicacion.id if n.publicacion else None,
                    'emisor_tipo': n.emisor.tipo,
                }
                for n in notificaciones
            ]
        }
        return JsonResponse(data)

    except Exception as e:
        print(f"Error obteniendo notificaciones: {e}")
        return JsonResponse({'notificaciones': [], 'count': 0})


# ─────────────────────────────────────────────────────────────
#  API: MARCAR LEÍDA
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def marcar_leida(request, notificacion_id):
    try:
        usuario_actual, _ = _get_usuario(request)
        notificacion = Notificacion.objects.get(
            id=notificacion_id,
            destinatario=usuario_actual
        )
        notificacion.marcar_como_leida()
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False})


# ─────────────────────────────────────────────────────────────
#  API: MARCAR TODAS LEÍDAS
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def marcar_todas_leidas(request):
    try:
        usuario_actual, _ = _get_usuario(request)
        Notificacion.objects.filter(
            destinatario=usuario_actual,
            leida=False
        ).update(leida=True)
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False})


# ─────────────────────────────────────────────────────────────
#  VISTA: LISTA COMPLETA DE NOTIFICACIONES
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def lista_notificaciones(request):
    usuario_actual, datos_usuario = _get_usuario(request)

    if not usuario_actual:
        return redirect('sesion:home')

    notificaciones = Notificacion.objects.filter(
        destinatario=usuario_actual
    ).select_related('emisor').order_by('-fecha_creacion')

    notificaciones.filter(leida=False).update(leida=True)

    context = {
        'notificaciones': notificaciones,
        'usuario': datos_usuario,
        'tipo_perfil': request.session.get('tipo_usuario'),
    }
    return render(request, 'notificaciones.html', context)


# ─────────────────────────────────────────────────────────────
#  API: SILENCIAR / ACTIVAR USUARIO EN CHAT
# ─────────────────────────────────────────────────────────────
@sesion_requerida
@require_POST
def toggle_silenciar_usuario(request):
    """
    Silencia o activa las notificaciones de mensajes de un usuario específico.
    Body JSON: { "emisor_id": <int> }
    Respuesta: { "success": true, "silenciado": true/false, "mensaje": "..." }
    """
    import json
    try:
        usuario_actual, _ = _get_usuario(request)
        if not usuario_actual:
            return JsonResponse({'success': False, 'error': 'No autenticado'}, status=403)

        data = json.loads(request.body)
        emisor_id = data.get('emisor_id')

        if not emisor_id:
            return JsonResponse({'success': False, 'error': 'emisor_id requerido'}, status=400)

        emisor = Usuario.objects.get(id=emisor_id)

        from .models import ChatSilenciado
        ahora_silenciado = ChatSilenciado.toggle(usuario=usuario_actual, emisor=emisor)

        return JsonResponse({
            'success': True,
            'silenciado': ahora_silenciado,
            'mensaje': f"🔕 {emisor.nombre} silenciado" if ahora_silenciado else f"🔔 {emisor.nombre} activado",
        })

    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en toggle_silenciar_usuario: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@sesion_requerida
@require_POST
def verificar_silenciado(request):
    """
    Verifica si el usuario actual tiene silenciado a otro.
    Body JSON: { "emisor_id": <int> }
    Respuesta: { "silenciado": true/false }
    Útil para que el frontend muestre el estado correcto del botón.
    """
    import json
    try:
        usuario_actual, _ = _get_usuario(request)
        if not usuario_actual:
            return JsonResponse({'silenciado': False})

        data = json.loads(request.body)
        emisor_id = data.get('emisor_id')
        emisor = Usuario.objects.get(id=emisor_id)

        from .models import ChatSilenciado
        silenciado = ChatSilenciado.esta_silenciado(usuario=usuario_actual, emisor=emisor)

        return JsonResponse({'silenciado': silenciado})

    except Exception:
        return JsonResponse({'silenciado': False})