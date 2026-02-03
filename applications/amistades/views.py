# applications/amistades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Amistad
from applications.usuarios.models import Usuario
# ⭐ Importar los modelos de perfil
from applications.registro.models import Aprendiz, Instructor, Bienestar


def obtener_usuario_actual(request):
    """Función helper para obtener el Usuario correcto basado en la sesión"""
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
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
    
    # Buscar el Usuario que coincida con el perfil
    try:
        usuario_actual = Usuario.objects.get(nombre=datos_usuario.nombre)
        print(f"✅ Usuario encontrado: ID {usuario_actual.id}, Nombre: {usuario_actual.nombre}")
        return usuario_actual
    except Usuario.DoesNotExist:
        print(f"❌ No se encontró Usuario para {datos_usuario.nombre}")
        return None
    except Usuario.MultipleObjectsReturned:
        # Si hay múltiples, usar también el email
        usuario_actual = Usuario.objects.get(
            nombre=datos_usuario.nombre,
            email=datos_usuario.email
        )
        return usuario_actual


@login_required
def enviar_solicitud(request, usuario_id):
    """Envía una solicitud de amistad"""
    receptor = get_object_or_404(Usuario, id=usuario_id)
    
    # ⭐ CORRECCIÓN: Usar la función helper
    emisor = obtener_usuario_actual(request)
    
    if not emisor:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    print(f"📤 Enviando solicitud: {emisor.nombre} (ID: {emisor.id}) → {receptor.nombre} (ID: {receptor.id})")
    
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
    
    # ⭐ CORRECCIÓN
    emisor = obtener_usuario_actual(request)
    
    if not emisor:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
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
    # ⭐ CORRECCIÓN
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    solicitud = get_object_or_404(Amistad, id=solicitud_id, receptor=usuario_actual)
    
    if solicitud.estado == Amistad.PENDIENTE:
        solicitud.estado = Amistad.ACEPTADA
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        messages.success(request, f"¡Ahora eres amigo de {solicitud.emisor.nombre}! 🎉")
    
    return redirect('sesion:amigos')


@login_required
def rechazar_solicitud(request, solicitud_id):
    """Rechaza y elimina una solicitud de amistad"""
    # ⭐ CORRECCIÓN
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    solicitud = get_object_or_404(Amistad, id=solicitud_id, receptor=usuario_actual)
    
    if solicitud.estado == Amistad.PENDIENTE:
        solicitud.delete()
        messages.success(request, "Solicitud rechazada.")
    
    return redirect('sesion:amigos')


@login_required
def eliminar_amigo(request, usuario_id):
    """Elimina una amistad"""
    # ⭐ CORRECCIÓN
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
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