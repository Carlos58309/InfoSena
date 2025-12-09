# applications/amistades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Amistad
from applications.usuarios.models import Usuario

@login_required
def enviar_solicitud(request, usuario_id):
    """Envía una solicitud de amistad"""
    receptor = get_object_or_404(Usuario, id=usuario_id)
    emisor = request.user.usuario
    
    # Verificar que no sea el mismo usuario
    if emisor == receptor:
        messages.error(request, "No puedes enviarte una solicitud a ti mismo.")
        return redirect('sesion:amigos')
    
    # Verificar si ya son amigos
    if Amistad.son_amigos(emisor, receptor):
        messages.info(request, f"Ya eres amigo de {receptor.nombre}.")
        return redirect('sesion:amigos')
    
    # Verificar si ya existe una solicitud pendiente
    if Amistad.solicitud_existe(emisor, receptor):
        messages.info(request, "Ya existe una solicitud pendiente con este usuario.")
        return redirect('sesion:amigos')
    
    # Crear la solicitud
    Amistad.objects.create(emisor=emisor, receptor=receptor)
    messages.success(request, f"Solicitud enviada a {receptor.nombre}.")
    
    return redirect('sesion:amigos')


@login_required
def cancelar_solicitud(request, usuario_id):
    """Cancela una solicitud de amistad enviada"""
    receptor = get_object_or_404(Usuario, id=usuario_id)
    emisor = request.user.usuario
    
    solicitud = Amistad.objects.filter(
        emisor=emisor, 
        receptor=receptor, 
        estado=Amistad.PENDIENTE
    ).first()
    
    if solicitud:
        solicitud.delete()
        messages.success(request, "Solicitud cancelada.")
    
    return redirect('sesion:amigos')


@login_required
def aceptar_solicitud(request, solicitud_id):
    """Acepta una solicitud de amistad"""
    solicitud = get_object_or_404(Amistad, id=solicitud_id, receptor=request.user.usuario)
    
    if solicitud.estado == Amistad.PENDIENTE:
        solicitud.estado = Amistad.ACEPTADA
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        messages.success(request, f"Ahora eres amigo de {solicitud.emisor.nombre}.")
    
    return redirect('sesion:amigos')


@login_required
def rechazar_solicitud(request, solicitud_id):
    """Rechaza y elimina una solicitud de amistad"""
    solicitud = get_object_or_404(Amistad, id=solicitud_id, receptor=request.user.usuario)
    
    if solicitud.estado == Amistad.PENDIENTE:
        solicitud.delete()
        messages.success(request, "Solicitud rechazada.")
    
    return redirect('sesion:amigos')


@login_required
def eliminar_amigo(request, usuario_id):
    """Elimina una amistad"""
    usuario_actual = request.user.usuario
    otro_usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Buscar la amistad en ambas direcciones
    amistad = Amistad.objects.filter(
        Q(emisor=usuario_actual, receptor=otro_usuario, estado=Amistad.ACEPTADA) |
        Q(emisor=otro_usuario, receptor=usuario_actual, estado=Amistad.ACEPTADA)
    ).first()
    
    if amistad:
        amistad.delete()
        messages.success(request, f"Has eliminado a {otro_usuario.nombre} de tus amigos.")
    
    return redirect('sesion:amigos')


@login_required
def amigos_view(request):
    """Vista principal de amigos"""
    usuario_actual = request.user.usuario
    
    # Solicitudes recibidas (pendientes)
    solicitudes_recibidas = Amistad.objects.filter(
        receptor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('emisor')
    
    # Solicitudes enviadas (pendientes)
    solicitudes_enviadas = Amistad.objects.filter(
        emisor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('receptor')
    
    # Crear un set de IDs de usuarios con solicitud pendiente
    ids_con_solicitud = set()
    for sol in solicitudes_enviadas:
        ids_con_solicitud.add(sol.receptor.id)
    
    # Amigos aceptados
    amigos = Amistad.obtener_amigos(usuario_actual)
    
    # IDs de amigos
    ids_amigos = {amigo.id for amigo in amigos}
    
    # Sugerencias (usuarios que no son amigos y sin solicitud pendiente)
    sugerencias = Usuario.objects.exclude(
        id=usuario_actual.id
    ).exclude(
        id__in=ids_amigos
    ).exclude(
        id__in=ids_con_solicitud
    )
    
    # Excluir también a quienes nos enviaron solicitud
    ids_solicitudes_recibidas = {sol.emisor.id for sol in solicitudes_recibidas}
    sugerencias = sugerencias.exclude(id__in=ids_solicitudes_recibidas)
    
    context = {
        'solicitudes_recibidas': solicitudes_recibidas,
        'solicitudes_enviadas_ids': ids_con_solicitud,
        'sugerencias': sugerencias,
        'amigos': amigos,
    }
    
    return render(request, 'amigos.html', context)