# applications/notificaciones/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.amistades.models import Amistad
from applications.publicaciones.models import Publicacion, Comentario, Like
from applications.chat.models import Mensaje
from applications.usuarios.models import Usuario
from .models import Notificacion


def _usuario_desde_documento(numero_documento):
    try:
        return Usuario.objects.get(documento=numero_documento)
    except Usuario.DoesNotExist:
        return None
    except Usuario.MultipleObjectsReturned:
        return Usuario.objects.filter(documento=numero_documento).first()


def _esta_silenciado(destinatario, emisor):
    """
    Verifica si el destinatario tiene silenciado al emisor.
    Importación diferida para evitar circular imports.
    """
    try:
        from .models import ChatSilenciado
        return ChatSilenciado.esta_silenciado(usuario=destinatario, emisor=emisor)
    except Exception:
        return False


# ============================================================
# SOLICITUD DE AMISTAD
# ============================================================
@receiver(post_save, sender=Amistad)
def notificar_solicitud_amistad(sender, instance, created, **kwargs):
    if created and instance.estado == Amistad.PENDIENTE:
        try:
            Notificacion.objects.create(
                destinatario=instance.receptor,
                emisor=instance.emisor,
                tipo='solicitud_amistad',
                mensaje=f"{instance.emisor.nombre} te ha enviado una solicitud de amistad"
            )
        except Exception as e:
            print(f"❌ Error en notificar_solicitud_amistad: {e}")


# ============================================================
# AMISTAD ACEPTADA
# ============================================================
@receiver(post_save, sender=Amistad)
def notificar_amistad_aceptada(sender, instance, created, **kwargs):
    if not created and instance.estado == Amistad.ACEPTADA:
        try:
            Notificacion.objects.create(
                destinatario=instance.emisor,
                emisor=instance.receptor,
                tipo='amistad_aceptada',
                mensaje=f"{instance.receptor.nombre} ha aceptado tu solicitud de amistad"
            )
        except Exception as e:
            print(f"❌ Error en notificar_amistad_aceptada: {e}")


# ============================================================
# NUEVA PUBLICACIÓN
# ============================================================
@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        usuario_emisor = _usuario_desde_documento(instance.autor.numero_documento)
        if not usuario_emisor:
            print(f"⚠️ No se encontró Usuario para el autor de la publicación: {instance.autor}")
            return

        amigos = Amistad.obtener_amigos(usuario_emisor)

        categorias_emoji = {
            'salud': '🏥', 'bienestar': '🌟',
            'evento': '📅', 'informacion': '📢', 'otro': '📝'
        }
        emoji = categorias_emoji.get(instance.categoria, '📝')
        titulo_corto = instance.titulo[:50] + '...' if len(instance.titulo) > 50 else instance.titulo

        notificaciones = []
        for amigo in amigos:
            if amigo.id == usuario_emisor.id:
                continue
            notificaciones.append(Notificacion(
                destinatario=amigo,
                emisor=usuario_emisor,
                tipo='nueva_publicacion',
                mensaje=f"{emoji} {instance.autor.nombre} publicó: {titulo_corto}",
                publicacion=instance
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)
            print(f"✅ {len(notificaciones)} notificaciones de publicación creadas")

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_nueva_publicacion: {e}")
        traceback.print_exc()


# ============================================================
# NUEVO COMENTARIO
# ============================================================
@receiver(post_save, sender=Comentario)
def notificar_comentario(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        autor_perfil = instance.content_object
        if not autor_perfil:
            print("⚠️ No se pudo obtener el autor del comentario")
            return

        usuario_emisor = _usuario_desde_documento(autor_perfil.numero_documento)
        if not usuario_emisor:
            return

        autor_publicacion_perfil = instance.publicacion.autor
        usuario_destinatario = _usuario_desde_documento(autor_publicacion_perfil.numero_documento)
        if not usuario_destinatario:
            return

        if usuario_emisor.id == usuario_destinatario.id:
            return

        contenido_corto = instance.contenido[:50] + '...' if len(instance.contenido) > 50 else instance.contenido

        Notificacion.objects.create(
            destinatario=usuario_destinatario,
            emisor=usuario_emisor,
            tipo='comentario',
            mensaje=f"💬 {autor_perfil.nombre} comentó en tu publicación: \"{contenido_corto}\"",
            publicacion=instance.publicacion
        )

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_comentario: {e}")
        traceback.print_exc()


# ============================================================
# NUEVO LIKE
# ============================================================
@receiver(post_save, sender=Like)
def notificar_like(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        usuario_like_perfil = instance.content_object
        if not usuario_like_perfil:
            return

        usuario_emisor = _usuario_desde_documento(usuario_like_perfil.numero_documento)
        if not usuario_emisor:
            return

        autor_publicacion_perfil = instance.publicacion.autor
        usuario_destinatario = _usuario_desde_documento(autor_publicacion_perfil.numero_documento)
        if not usuario_destinatario:
            return

        if usuario_emisor.id == usuario_destinatario.id:
            return

        titulo_corto = instance.publicacion.titulo[:40] + '...' if len(instance.publicacion.titulo) > 40 else instance.publicacion.titulo

        Notificacion.objects.create(
            destinatario=usuario_destinatario,
            emisor=usuario_emisor,
            tipo='like',
            mensaje=f"❤️ A {usuario_like_perfil.nombre} le gustó tu publicación: \"{titulo_corto}\"",
            publicacion=instance.publicacion
        )

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_like: {e}")
        traceback.print_exc()


# ============================================================
# NUEVO MENSAJE DE CHAT
# Respeta la configuración de silenciar: si el destinatario
# tiene silenciado al autor, no se crea la notificación.
# ============================================================
@receiver(post_save, sender=Mensaje)
def notificar_nuevo_mensaje(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        chat = instance.chat
        autor = instance.autor  # Ya es un objeto Usuario

        destinatarios = chat.participantes.exclude(id=autor.id)

        contenido_corto = instance.contenido[:60] + '...' if len(instance.contenido) > 60 else instance.contenido

        if chat.is_group:
            nombre_chat = chat.nombre_grupo or "un grupo"
            mensaje_notif = f"💬 {autor.nombre} en {nombre_chat}: \"{contenido_corto}\""
        else:
            mensaje_notif = f"💬 {autor.nombre} te envió un mensaje: \"{contenido_corto}\""

        notificaciones = []
        silenciados_omitidos = 0

        for destinatario in destinatarios:
            # ── Verificar si este destinatario tiene silenciado al autor ──
            if _esta_silenciado(destinatario=destinatario, emisor=autor):
                silenciados_omitidos += 1
                continue  # No crear notificación para este destinatario

            notificaciones.append(Notificacion(
                destinatario=destinatario,
                emisor=autor,
                tipo='mensaje',
                mensaje=mensaje_notif,
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)
            print(f"✅ {len(notificaciones)} notificaciones de mensaje creadas (omitidos silenciados: {silenciados_omitidos})")
        elif silenciados_omitidos:
            print(f"🔕 Mensaje enviado pero todos los destinatarios tienen silenciado al autor")

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_nuevo_mensaje: {e}")
        traceback.print_exc()