# applications/chat/views.py
# VERSIÓN ADAPTADA PARA TEMPLATES GLOBALES

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max, Count, Prefetch
from django.utils import timezone

from applications.usuarios.models import Usuario
from applications.amistades.models import Amistad
from .models import Chat, Mensaje


def obtener_usuario_actual(request):
    """
    Función helper para obtener el Usuario actual desde la sesión
    """
    from applications.registro.models import Aprendiz, Instructor, Bienestar
    
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    if not usuario_id or not tipo_perfil:
        return None
    
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            return None
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        return None
    
    try:
        usuario_actual = Usuario.objects.get(documento=datos_usuario.numero_documento)
        return usuario_actual
    except Usuario.DoesNotExist:
        return None
    except Usuario.MultipleObjectsReturned:
        return Usuario.objects.filter(documento=datos_usuario.numero_documento).first()


@login_required
def lista_chats(request):
    """
    Vista principal de chats - Muestra panel de conversaciones
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:home')
    
    # Obtener todos los chats
    todos_los_chats = Chat.objects.filter(
        participantes=usuario_actual
    ).prefetch_related(
        'participantes',
        Prefetch(
            'mensajes',
            queryset=Mensaje.objects.order_by('-enviado')[:1],
            to_attr='ultimo_mensaje_obj'
        )
    ).annotate(
        ultimo_mensaje_fecha=Max('mensajes__enviado')
    ).order_by('-ultimo_mensaje_fecha')
    
    # Enriquecer chats
    chats_enriquecidos = []
    for c in todos_los_chats:
        ultimo_msg = c.ultimo_mensaje_obj[0] if c.ultimo_mensaje_obj else None
        mensajes_no_leidos = c.mensajes_no_leidos_para_usuario(usuario_actual)
        
        chats_enriquecidos.append({
            'chat': c,
            'nombre': c.obtener_nombre_para_usuario(usuario_actual),
            'foto': c.obtener_foto_para_usuario(usuario_actual),
            'ultimo_mensaje': ultimo_msg,
            'mensajes_no_leidos': mensajes_no_leidos,
            'activo': False  # Ningún chat seleccionado
        })
    
    # Obtener amigos para iniciar chats
    amigos = Amistad.obtener_amigos(usuario_actual)
    
    context = {
        'usuario': usuario_actual,
        'chats': chats_enriquecidos,
        'amigos': amigos,
        'chat': None,  # ⬅️ Sin chat seleccionado
        'mensajes': [],
        'chat_nombre': None,
        'chat_foto': None,
        'is_group': False,
    }
    
    # ⬅️ AHORA USA EL MISMO TEMPLATE QUE chat_room
    return render(request, 'chat.html', context)


@login_required
def chat_room(request, chat_id):
    """
    Vista de sala de chat individual
    TEMPLATE: chat.html (en carpeta templates/ global)
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:home')
    
    # Obtener chat
    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    
    # Obtener mensajes
    mensajes = chat.mensajes.select_related('autor').order_by('enviado')
    
    # Marcar mensajes como vistos
    mensajes_no_vistos = mensajes.filter(visto=False).exclude(autor=usuario_actual)
    for mensaje in mensajes_no_vistos:
        mensaje.marcar_como_visto()
    
    # Obtener todos los chats para la barra lateral
    todos_los_chats = Chat.objects.filter(
        participantes=usuario_actual
    ).annotate(
        ultimo_mensaje_fecha=Max('mensajes__enviado')
    ).order_by('-ultimo_mensaje_fecha')
    
    chats_enriquecidos = []
    for c in todos_los_chats:
        ultimo_msg = c.ultimo_mensaje()
        mensajes_no_leidos = c.mensajes_no_leidos_para_usuario(usuario_actual)
        
        chats_enriquecidos.append({
            'chat': c,
            'nombre': c.obtener_nombre_para_usuario(usuario_actual),
            'foto': c.obtener_foto_para_usuario(usuario_actual),
            'ultimo_mensaje': ultimo_msg,
            'mensajes_no_leidos': mensajes_no_leidos,
            'activo': c.id == chat.id
        })
    
    context = {
        'usuario': usuario_actual,
        'chat': chat,
        'mensajes': mensajes,
        'chats': chats_enriquecidos,
        'chat_nombre': chat.obtener_nombre_para_usuario(usuario_actual),
        'chat_foto': chat.obtener_foto_para_usuario(usuario_actual),
        'is_group': chat.is_group,
    }
    
    # ⬅️ USANDO TU TEMPLATE GLOBAL
    return render(request, 'chat.html', context)


@login_required
def iniciar_chat(request, usuario_id):
    """
    Inicia un chat individual con otro usuario
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:home')
    
    # Verificar que el otro usuario existe
    otro_usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Verificar que son amigos
    if not Amistad.son_amigos(usuario_actual, otro_usuario):
        messages.error(request, "Solo puedes chatear con tus amigos.")
        return redirect('sesion:amigos')
    
    # Obtener o crear chat
    chat = Chat.obtener_o_crear_chat_individual(usuario_actual, otro_usuario)
    
    # Redirigir a la sala de chat
    # Ajusta el namespace según tu configuración:
    # - Si usas sesion: return redirect('sesion:chat_room', chat_id=chat.id)
    # - Si usas chat: return redirect('chat:chat_room', chat_id=chat.id)
    return redirect('sesion:chat_room', chat_id=chat.id)


@login_required
def enviar_mensaje(request, chat_id):
    """
    Envía un mensaje en un chat (para formularios sin WebSocket)
    """
    if request.method != 'POST':
        return redirect('sesion:chat_room', chat_id=chat_id)
    
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:home')
    
    # Obtener chat
    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    
    # Obtener contenido
    contenido = request.POST.get('contenido', '').strip()
    
    if contenido:
        # Crear mensaje
        Mensaje.objects.create(
            chat=chat,
            autor=usuario_actual,
            contenido=contenido
        )
        
        # Actualizar timestamp del chat
        chat.actualizado_en = timezone.now()
        chat.save(update_fields=['actualizado_en'])
    
    return redirect('sesion:chat_room', chat_id=chat_id)


@login_required
def crear_grupo(request):
    """
    Vista para crear un grupo de chat
    TEMPLATE: crear_grupo.html (en carpeta templates/ global)
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:home')
    
    if request.method == 'POST':
        nombre_grupo = request.POST.get('nombre_grupo')
        descripcion = request.POST.get('descripcion', '')
        participantes_ids = request.POST.getlist('participantes')
        
        if not nombre_grupo:
            messages.error(request, "El nombre del grupo es obligatorio.")
            return redirect('sesion:crear_grupo')
        
        if not participantes_ids:
            messages.error(request, "Debes seleccionar al menos un participante.")
            return redirect('sesion:crear_grupo')
        
        # Crear grupo
        grupo = Chat.crear_grupo(
            nombre=nombre_grupo,
            admin=usuario_actual,
            participantes_ids=participantes_ids,
            descripcion=descripcion
        )
        
        messages.success(request, f"Grupo '{nombre_grupo}' creado exitosamente.")
        return redirect('sesion:chat_room', chat_id=grupo.id)
    
    # GET - Mostrar formulario
    amigos = Amistad.obtener_amigos(usuario_actual)
    
    context = {
        'usuario': usuario_actual,
        'amigos': amigos,
    }
    
    # ⬅️ USANDO TU TEMPLATE GLOBAL
    return render(request, 'crear_grupo.html', context)


# ==========================================
# API ENDPOINTS PARA AJAX
# ==========================================

@login_required
def api_obtener_mensajes(request, chat_id):
    """
    API para obtener mensajes de un chat (para polling)
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        return JsonResponse({'error': 'Usuario no identificado'}, status=403)
    
    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    
    # Obtener ID del último mensaje conocido por el cliente
    ultimo_id = request.GET.get('ultimo_id', 0)
    
    # Obtener mensajes nuevos
    mensajes_nuevos = chat.mensajes.filter(
        id__gt=ultimo_id
    ).select_related('autor').order_by('enviado')
    
    # Marcar como vistos los que no son del usuario actual
    for mensaje in mensajes_nuevos:
        if mensaje.autor != usuario_actual:
            mensaje.marcar_como_visto()
    
    # Serializar mensajes
    mensajes_data = []
    for mensaje in mensajes_nuevos:
        mensajes_data.append({
            'id': mensaje.id,
            'autor_id': mensaje.autor.id,
            'autor_nombre': mensaje.autor.nombre,
            'contenido': mensaje.contenido,
            'enviado': mensaje.enviado.isoformat(),
            'tiempo_transcurrido': mensaje.tiempo_transcurrido(),
            'es_mio': mensaje.autor.id == usuario_actual.id,
        })
    
    return JsonResponse({
        'mensajes': mensajes_data,
        'total': len(mensajes_data)
    })


@login_required
def api_enviar_mensaje(request, chat_id):
    """
    API para enviar un mensaje vía AJAX
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        return JsonResponse({'error': 'Usuario no identificado'}, status=403)
    
    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    
    import json
    data = json.loads(request.body)
    contenido = data.get('contenido', '').strip()
    
    if not contenido:
        return JsonResponse({'error': 'El mensaje no puede estar vacío'}, status=400)
    
    # Crear mensaje
    mensaje = Mensaje.objects.create(
        chat=chat,
        autor=usuario_actual,
        contenido=contenido
    )
    
    # Actualizar timestamp del chat
    chat.actualizado_en = timezone.now()
    chat.save(update_fields=['actualizado_en'])
    
    return JsonResponse({
        'success': True,
        'mensaje': {
            'id': mensaje.id,
            'autor_id': mensaje.autor.id,
            'autor_nombre': mensaje.autor.nombre,
            'contenido': mensaje.contenido,
            'enviado': mensaje.enviado.isoformat(),
            'tiempo_transcurrido': mensaje.tiempo_transcurrido(),
        }
    })