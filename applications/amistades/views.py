# applications/amistades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Amistad
from applications.usuarios.models import Usuario
from applications.registro.models import Aprendiz, Instructor, Bienestar


def obtener_usuario_actual(request):
    """
    Función helper para obtener el Usuario correcto basado en la sesión.
    Retorna solo el objeto Usuario (no la tupla).
    """
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    print(f"🔍 [Amistades] obtener_usuario_actual - documento: {usuario_id}, tipo: {tipo_perfil}")
    
    if not usuario_id or not tipo_perfil:
        print("❌ No hay datos de sesión")
        return None
    
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            print(f"❌ tipo_perfil no reconocido: {tipo_perfil}")
            return None
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist) as e:
        print(f"❌ Error al buscar perfil: {e}")
        return None
    
    # Buscar el Usuario correspondiente
    try:
        usuario_actual = Usuario.objects.get(documento=datos_usuario.numero_documento)
        print(f"✅ Usuario encontrado: ID {usuario_actual.id}, Nombre: {usuario_actual.nombre}")
        return usuario_actual
    except Usuario.DoesNotExist:
        print(f"❌ No existe Usuario con documento: {datos_usuario.numero_documento}")
        return None
    except Usuario.MultipleObjectsReturned:
        print(f"⚠️ Múltiples Usuarios con documento: {datos_usuario.numero_documento}")
        usuario_actual = Usuario.objects.filter(documento=datos_usuario.numero_documento).first()
        return usuario_actual


@login_required
def enviar_solicitud(request, usuario_id):
    """Envía una solicitud de amistad"""
    
    print(f"\n📤 ENVIAR SOLICITUD a usuario_id: {usuario_id}")
    
    receptor = get_object_or_404(Usuario, id=usuario_id)
    print(f"   Receptor: {receptor.nombre} (ID: {receptor.id})")
    
    emisor = obtener_usuario_actual(request)
    
    if not emisor:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    print(f"   Emisor: {emisor.nombre} (ID: {emisor.id})")
    
    # Verificar que no sea el mismo usuario
    if emisor.id == receptor.id:
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
    solicitud = Amistad.objects.create(emisor=emisor, receptor=receptor)
    print(f"✅ Solicitud creada: ID {solicitud.id}")
    
    messages.success(request, f"Solicitud enviada a {receptor.nombre}.")
    return redirect('sesion:amigos')


@login_required
def cancelar_solicitud(request, usuario_id):
    """Cancela una solicitud de amistad enviada"""
    
    print(f"\n❌ CANCELAR SOLICITUD a usuario_id: {usuario_id}")
    
    receptor = get_object_or_404(Usuario, id=usuario_id)
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
        print(f"✅ Solicitud cancelada")
        messages.success(request, "Solicitud cancelada.")
    else:
        print(f"⚠️ No se encontró la solicitud")
        messages.warning(request, "No se encontró la solicitud.")
    
    return redirect('sesion:amigos')


@login_required
def aceptar_solicitud(request, solicitud_id):
    """Acepta una solicitud de amistad"""
    
    print(f"\n✅ ACEPTAR SOLICITUD ID: {solicitud_id}")
    
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    solicitud = get_object_or_404(
        Amistad,
        id=solicitud_id,
        receptor=usuario_actual,
        estado=Amistad.PENDIENTE
    )
    
    print(f"   Solicitud de: {solicitud.emisor.nombre} → {solicitud.receptor.nombre}")
    
    solicitud.estado = Amistad.ACEPTADA
    solicitud.fecha_respuesta = timezone.now()
    solicitud.save()
    
    print(f"✅ Solicitud aceptada")
    messages.success(request, f"¡Ahora eres amigo de {solicitud.emisor.nombre}! 🎉")
    
    return redirect('sesion:amigos')


@login_required
def rechazar_solicitud(request, solicitud_id):
    """Rechaza y elimina una solicitud de amistad"""
    
    print(f"\n❌ RECHAZAR SOLICITUD ID: {solicitud_id}")
    
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    solicitud = get_object_or_404(
        Amistad,
        id=solicitud_id,
        receptor=usuario_actual,
        estado=Amistad.PENDIENTE
    )
    
    print(f"   Rechazando solicitud de: {solicitud.emisor.nombre}")
    
    solicitud.delete()
    print(f"✅ Solicitud rechazada")
    
    messages.success(request, "Solicitud rechazada.")
    return redirect('sesion:amigos')


@login_required
def eliminar_amigo(request, usuario_id):
    """Elimina una amistad"""
    
    print(f"\n🗑️ ELIMINAR AMIGO usuario_id: {usuario_id}")
    
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect('sesion:amigos')
    
    otro_usuario = get_object_or_404(Usuario, id=usuario_id)
    print(f"   Eliminando amistad con: {otro_usuario.nombre}")
    
    # Buscar la amistad en ambas direcciones
    amistad = Amistad.objects.filter(
        Q(emisor=usuario_actual, receptor=otro_usuario, estado=Amistad.ACEPTADA) |
        Q(emisor=otro_usuario, receptor=usuario_actual, estado=Amistad.ACEPTADA)
    ).first()
    
    if amistad:
        amistad.delete()
        print(f"✅ Amistad eliminada")
        messages.success(request, f"Has eliminado a {otro_usuario.nombre} de tus amigos.")
    else:
        print(f"⚠️ No se encontró la amistad")
        messages.warning(request, "No se encontró la amistad.")
    
    return redirect('sesion:amigos')