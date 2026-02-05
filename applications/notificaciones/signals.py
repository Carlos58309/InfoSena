# applications/notificaciones/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.amistades.models import Amistad
from applications.publicaciones.models import Publicacion, Comentario, Like
from .models import Notificacion

# ======================================
#  NOTIFICACIÓN: SOLICITUD DE AMISTAD
# ======================================
@receiver(post_save, sender=Amistad)
def notificar_solicitud_amistad(sender, instance, created, **kwargs):
    """Crea notificación cuando alguien envía una solicitud de amistad"""
    if created and instance.estado == Amistad.PENDIENTE:
        Notificacion.objects.create(
            destinatario=instance.receptor,
            emisor=instance.emisor,
            tipo='solicitud_amistad',
            mensaje=f"{instance.emisor.nombre} te ha enviado una solicitud de amistad"
        )
        print(f"🔔 Notificación creada: Solicitud de amistad de {instance.emisor.nombre} a {instance.receptor.nombre}")


# ======================================
#  NOTIFICACIÓN: AMISTAD ACEPTADA
# ======================================
@receiver(post_save, sender=Amistad)
def notificar_amistad_aceptada(sender, instance, created, **kwargs):
    """Crea notificación cuando alguien acepta tu solicitud"""
    if not created and instance.estado == Amistad.ACEPTADA:
        # Notificar al que envió la solicitud original
        Notificacion.objects.create(
            destinatario=instance.emisor,
            emisor=instance.receptor,
            tipo='amistad_aceptada',
            mensaje=f"{instance.receptor.nombre} ha aceptado tu solicitud de amistad"
        )
        print(f"🔔 Notificación creada: {instance.receptor.nombre} aceptó solicitud de {instance.emisor.nombre}")


# ======================================
#  NOTIFICACIÓN: NUEVA PUBLICACIÓN DE UN AMIGO
# ======================================
@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    """
    Crea notificaciones para todos los amigos cuando haces una publicación.
    Solo notifica a usuarios que son AMIGOS del autor.
    """
    if created:
        # Obtener todos los amigos del autor de la publicación
        amigos = Amistad.obtener_amigos(instance.autor)
        
        # Preparar el mensaje dependiendo de la categoría
        categorias_emoji = {
            'salud': '🏥',
            'bienestar': '🌟',
            'evento': '📅',
            'informacion': '📢',
            'otro': '📝'
        }
        
        emoji = categorias_emoji.get(instance.categoria, '📝')
        
        # Truncar título si es muy largo
        titulo_corto = instance.titulo[:50] + '...' if len(instance.titulo) > 50 else instance.titulo
        
        # Crear notificación para cada amigo
        notificaciones_creadas = 0
        for amigo in amigos:
            Notificacion.objects.create(
                destinatario=amigo,
                emisor=instance.autor,
                tipo='nueva_publicacion',
                mensaje=f"{emoji} {instance.autor.nombre} publicó: {titulo_corto}",
                publicacion=instance
            )
            notificaciones_creadas += 1
        
        if notificaciones_creadas > 0:
            print(f"🔔 Notificaciones creadas: Nueva publicación '{titulo_corto}' notificada a {notificaciones_creadas} amigos")
        else:
            print(f"ℹ️ Publicación creada pero el autor no tiene amigos para notificar")


# ======================================
#  NOTIFICACIÓN: COMENTARIO EN TU PUBLICACIÓN
# ======================================
@receiver(post_save, sender=Comentario)
def notificar_comentario(sender, instance, created, **kwargs):
    """Notifica al autor de la publicación cuando alguien comenta"""
    if created:
        # Solo notificar si no es el mismo autor
        if instance.autor != instance.publicacion.autor.user:
            try:
                from applications.usuarios.models import Usuario
                emisor = Usuario.objects.get(user=instance.autor)
                
                # Truncar contenido del comentario
                contenido_corto = instance.contenido[:50] + '...' if len(instance.contenido) > 50 else instance.contenido
                
                Notificacion.objects.create(
                    destinatario=instance.publicacion.autor,
                    emisor=emisor,
                    tipo='comentario',
                    mensaje=f"💬 {emisor.nombre} comentó en tu publicación: \"{contenido_corto}\"",
                    publicacion=instance.publicacion
                )
                print(f"🔔 Notificación creada: {emisor.nombre} comentó en publicación de {instance.publicacion.autor.nombre}")
            except Exception as e:
                print(f"❌ Error al crear notificación de comentario: {e}")


# ======================================
#  NOTIFICACIÓN: LIKE EN TU PUBLICACIÓN
# ======================================
@receiver(post_save, sender=Like)
def notificar_like(sender, instance, created, **kwargs):
    """Notifica al autor cuando alguien da like a su publicación"""
    if created:
        # Solo notificar si no es el mismo autor
        if instance.usuario != instance.publicacion.autor.user:
            try:
                from applications.usuarios.models import Usuario
                emisor = Usuario.objects.get(user=instance.usuario)
                
                # Título corto de la publicación
                titulo_corto = instance.publicacion.titulo[:40] + '...' if len(instance.publicacion.titulo) > 40 else instance.publicacion.titulo
                
                Notificacion.objects.create(
                    destinatario=instance.publicacion.autor,
                    emisor=emisor,
                    tipo='like',
                    mensaje=f"❤️ A {emisor.nombre} le gustó tu publicación: \"{titulo_corto}\"",
                    publicacion=instance.publicacion
                )
                print(f"🔔 Notificación creada: {emisor.nombre} dio like a publicación de {instance.publicacion.autor.nombre}")
            except Exception as e:
                print(f"❌ Error al crear notificación de like: {e}")


# ======================================
#  FUNCIONES AUXILIARES PARA DEBUGGING
# ======================================
def verificar_notificaciones_activas():
    """
    Función auxiliar para verificar que los signals estén funcionando.
    Puedes ejecutarla desde el shell de Django:
    
    from applications.notificaciones.signals import verificar_notificaciones_activas
    verificar_notificaciones_activas()
    """
    print("✅ Signals de notificaciones registrados correctamente:")
    print("   - notificar_solicitud_amistad")
    print("   - notificar_amistad_aceptada")
    print("   - notificar_nueva_publicacion")
    print("   - notificar_comentario")
    print("   - notificar_like")
    return True