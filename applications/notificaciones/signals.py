from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.amistades.models import Amistad
from applications.publicaciones.models import Publicacion, Comentario, Like
from .models import Notificacion


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


@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    if created:
        try:
            amigos = Amistad.obtener_amigos(instance.autor)
            categorias_emoji = {
                'salud': '🏥', 'bienestar': '🌟',
                'evento': '📅', 'informacion': '📢', 'otro': '📝'
            }
            emoji = categorias_emoji.get(instance.categoria, '📝')
            titulo_corto = instance.titulo[:50] + '...' if len(instance.titulo) > 50 else instance.titulo
            for amigo in amigos:
                Notificacion.objects.create(
                    destinatario=amigo,
                    emisor=instance.autor,
                    tipo='nueva_publicacion',
                    mensaje=f"{emoji} {instance.autor.nombre} publicó: {titulo_corto}",
                    publicacion=instance
                )
        except Exception as e:
            print(f"❌ Error en notificar_nueva_publicacion: {e}")


@receiver(post_save, sender=Comentario)
def notificar_comentario(sender, instance, created, **kwargs):
    if created:
        try:
            autor_comentario = instance.autor
            autor_publicacion = instance.publicacion.autor
            if instance.object_id == autor_publicacion.numero_documento:
                return
            contenido_corto = instance.contenido[:50] + '...' if len(instance.contenido) > 50 else instance.contenido
            Notificacion.objects.create(
                destinatario=autor_publicacion,
                emisor=autor_publicacion,
                tipo='comentario',
                mensaje=f"💬 {autor_comentario.nombre} comentó: \"{contenido_corto}\"",
                publicacion=instance.publicacion
            )
        except Exception as e:
            print(f"❌ Error en notificar_comentario: {e}")


@receiver(post_save, sender=Like)
def notificar_like(sender, instance, created, **kwargs):
    if created:
        try:
            usuario_like = instance.usuario
            autor_publicacion = instance.publicacion.autor
            if instance.object_id == autor_publicacion.numero_documento:
                return
            titulo_corto = instance.publicacion.titulo[:40] + '...' if len(instance.publicacion.titulo) > 40 else instance.publicacion.titulo
            Notificacion.objects.create(
                destinatario=autor_publicacion,
                emisor=autor_publicacion,
                tipo='like',
                mensaje=f"❤️ A {usuario_like.nombre} le gustó tu publicación: \"{titulo_corto}\"",
                publicacion=instance.publicacion
            )
        except Exception as e:
            print(f"❌ Error en notificar_like: {e}")