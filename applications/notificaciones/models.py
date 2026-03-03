# applications/notificaciones/models.py
# ─── AGREGA ESTE MODELO AL FINAL DE TU models.py ACTUAL ───────────────────────
# (conserva todo lo que ya tienes: Notificacion, etc.)

from django.db import models
from django.utils import timezone
from applications.usuarios.models import Usuario
from applications.publicaciones.models import Publicacion


class Notificacion(models.Model):
    TIPOS = [
        ('solicitud_amistad', 'Solicitud de amistad'),
        ('amistad_aceptada',  'Amistad aceptada'),
        ('nueva_publicacion', 'Nueva publicación'),
        ('comentario',        'Nuevo comentario'),
        ('like',              'Le gustó tu publicación'),
        ('mensaje',           'Nuevo mensaje'),
    ]

    destinatario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas'
    )
    emisor = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='notificaciones_enviadas'
    )
    tipo        = models.CharField(max_length=30, choices=TIPOS)
    mensaje     = models.TextField()
    publicacion = models.ForeignKey(
        Publicacion, on_delete=models.CASCADE, null=True, blank=True
    )
    leida        = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"{self.emisor.nombre} → {self.destinatario.nombre}: {self.tipo}"

    def marcar_como_leida(self):
        self.leida = True
        self.save()


# ─────────────────────────────────────────────────────────────────────────────

class ChatSilenciado(models.Model):
    """
    Cuando un usuario silencia a otro en el chat,
    no recibirá notificaciones de mensajes de esa persona.
    Solo afecta notificaciones — los mensajes siguen llegando.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='usuarios_silenciados',
        verbose_name='Usuario que silencia'
    )
    silenciado = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='silenciado_por',
        verbose_name='Usuario silenciado'
    )
    silenciado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_silenciado'
        unique_together = ('usuario', 'silenciado')
        verbose_name = 'Chat Silenciado'
        verbose_name_plural = 'Chats Silenciados'

    def __str__(self):
        return f"{self.usuario.nombre} silenció a {self.silenciado.nombre}"

    @classmethod
    def esta_silenciado(cls, usuario, emisor):
        """Devuelve True si 'usuario' tiene silenciado a 'emisor'."""
        return cls.objects.filter(usuario=usuario, silenciado=emisor).exists()

    @classmethod
    def silenciar(cls, usuario, emisor):
        cls.objects.get_or_create(usuario=usuario, silenciado=emisor)

    @classmethod
    def activar(cls, usuario, emisor):
        cls.objects.filter(usuario=usuario, silenciado=emisor).delete()

    @classmethod
    def toggle(cls, usuario, emisor):
        """Silencia o activa. Devuelve True si quedó silenciado."""
        obj, created = cls.objects.get_or_create(usuario=usuario, silenciado=emisor)
        if not created:
            obj.delete()
            return False
        return True