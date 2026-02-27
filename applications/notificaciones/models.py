# applications/notificaciones/models.py

from django.db import models
from applications.usuarios.models import Usuario
from applications.publicaciones.models import Publicacion


class Notificacion(models.Model):
    TIPOS = [
        ('solicitud_amistad', 'Solicitud de amistad'),
        ('amistad_aceptada',  'Amistad aceptada'),
        ('nueva_publicacion', 'Nueva publicación'),
        ('comentario',        'Nuevo comentario'),
        ('like',              'Le gustó tu publicación'),
        ('mensaje',           'Nuevo mensaje'),          # ← NUEVO
    ]

    # A quién va dirigida la notificación
    destinatario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones_recibidas'
    )

    # Quién generó la notificación
    emisor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones_enviadas'
    )

    tipo = models.CharField(max_length=30, choices=TIPOS)

    # Contenido de la notificación
    mensaje = models.TextField()

    # Relación opcional con publicación
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Estado
    leida = models.BooleanField(default=False)

    # Fecha
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