# applications/notificaciones/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.amistades.models import Amistad
from applications.publicaciones.models import Publicacion, Comentario, Like
from applications.chat.models import Mensaje
from applications.usuarios.models import Usuario
from .models import Notificacion


def _usuario_desde_documento(numero_documento):
    """
    Helper: devuelve el objeto Usuario a partir de un numero_documento.
    Retorna None si no se encuentra.
    """
    try:
        return Usuario.objects.get(documento=numero_documento)
    except Usuario.DoesNotExist:
        return None
    except Usuario.MultipleObjectsReturned:
        return Usuario.objects.filter(documento=numero_documento).first()


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
# El autor de la publicación es un objeto Bienestar/Instructor/Aprendiz
# (GenericForeignKey en Publicacion.autor), necesitamos convertirlo a Usuario
# para poder guardar la notificación, ya que Notificacion.emisor es FK a Usuario.
# ============================================================
@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        # Convertir autor (Bienestar/Instructor/Aprendiz) → Usuario
        usuario_emisor = _usuario_desde_documento(instance.autor.numero_documento)
        if not usuario_emisor:
            print(f"⚠️ No se encontró Usuario para el autor de la publicación: {instance.autor}")
            return

        # Obtener amigos del usuario emisor
        amigos = Amistad.obtener_amigos(usuario_emisor)

        categorias_emoji = {
            'salud': '🏥', 'bienestar': '🌟',
            'evento': '📅', 'informacion': '📢', 'otro': '📝'
        }
        emoji = categorias_emoji.get(instance.categoria, '📝')
        titulo_corto = instance.titulo[:50] + '...' if len(instance.titulo) > 50 else instance.titulo

        notificaciones = []
        for amigo in amigos:
            # Evitar notificarse a sí mismo
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
# Comentario usa GenericForeignKey (content_type + object_id)
# en lugar de un FK directo. object_id = numero_documento del autor.
# ============================================================
@receiver(post_save, sender=Comentario)
def notificar_comentario(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        # Obtener el autor del comentario desde GenericForeignKey
        # instance.content_object devuelve el Aprendiz/Instructor/Bienestar
        autor_perfil = instance.content_object  # objeto real del autor del comentario
        if not autor_perfil:
            print("⚠️ No se pudo obtener el autor del comentario")
            return

        usuario_emisor = _usuario_desde_documento(autor_perfil.numero_documento)
        if not usuario_emisor:
            print(f"⚠️ No se encontró Usuario para el autor del comentario")
            return

        # Autor de la publicación (también puede ser Bienestar, etc.)
        autor_publicacion_perfil = instance.publicacion.autor
        usuario_destinatario = _usuario_desde_documento(autor_publicacion_perfil.numero_documento)
        if not usuario_destinatario:
            print(f"⚠️ No se encontró Usuario para el autor de la publicación")
            return

        # No notificar si la persona se comenta a sí misma
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
        print(f"✅ Notificación de comentario creada: {autor_perfil.nombre} → {autor_publicacion_perfil.nombre}")

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_comentario: {e}")
        traceback.print_exc()


# ============================================================
# NUEVO LIKE
# Like también usa GenericForeignKey (content_type + object_id)
# ============================================================
@receiver(post_save, sender=Like)
def notificar_like(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        # Obtener el perfil del usuario que dio like desde GenericForeignKey
        usuario_like_perfil = instance.content_object  # Aprendiz/Instructor/Bienestar
        if not usuario_like_perfil:
            print("⚠️ No se pudo obtener el usuario que dio like")
            return

        usuario_emisor = _usuario_desde_documento(usuario_like_perfil.numero_documento)
        if not usuario_emisor:
            print(f"⚠️ No se encontró Usuario para quien dio like")
            return

        # Autor de la publicación
        autor_publicacion_perfil = instance.publicacion.autor
        usuario_destinatario = _usuario_desde_documento(autor_publicacion_perfil.numero_documento)
        if not usuario_destinatario:
            print(f"⚠️ No se encontró Usuario para el autor de la publicación")
            return

        # No notificar si la persona da like a su propia publicación
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
        print(f"✅ Notificación de like creada: {usuario_like_perfil.nombre} → {autor_publicacion_perfil.nombre}")

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_like: {e}")
        traceback.print_exc()


# ============================================================
# NUEVO MENSAJE DE CHAT
# Cuando alguien envía un mensaje, notificar a todos los demás
# participantes del chat (excepto al autor).
# ============================================================
@receiver(post_save, sender=Mensaje)
def notificar_nuevo_mensaje(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        chat = instance.chat
        autor = instance.autor  # Ya es un objeto Usuario

        # Obtener todos los participantes excepto el autor
        destinatarios = chat.participantes.exclude(id=autor.id)

        contenido_corto = instance.contenido[:60] + '...' if len(instance.contenido) > 60 else instance.contenido

        # Nombre del chat: si es grupal usar el nombre del grupo, si no usar el nombre del autor
        if chat.is_group:
            nombre_chat = chat.nombre if hasattr(chat, 'nombre') and chat.nombre else "un grupo"
            mensaje_notif = f"💬 {autor.nombre} en {nombre_chat}: \"{contenido_corto}\""
        else:
            mensaje_notif = f"💬 {autor.nombre} te envió un mensaje: \"{contenido_corto}\""

        notificaciones = []
        for destinatario in destinatarios:
            notificaciones.append(Notificacion(
                destinatario=destinatario,
                emisor=autor,
                tipo='mensaje',
                mensaje=mensaje_notif,
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)
            print(f"✅ {len(notificaciones)} notificaciones de mensaje creadas para el chat {chat.id}")

    except Exception as e:
        import traceback
        print(f"❌ Error en notificar_nuevo_mensaje: {e}")
        traceback.print_exc()