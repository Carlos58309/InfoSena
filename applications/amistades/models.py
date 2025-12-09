# applications/amistades/models.py

from django.db import models
from django.conf import settings
from applications.usuarios.models import Usuario

class Amistad(models.Model):
    PENDIENTE = 'pendiente'
    ACEPTADA = 'aceptada'
    RECHAZADA = 'rechazada'
    
    ESTADOS = [
        (PENDIENTE, 'Pendiente'),
        (ACEPTADA, 'Aceptada'),
        (RECHAZADA, 'Rechazada'),
    ]

    # Quien envía la solicitud
    emisor = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_enviadas'
    )
    
    # Quien recibe la solicitud
    receptor = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_recibidas'
    )
    
    estado = models.CharField(
        max_length=10, 
        choices=ESTADOS, 
        default=PENDIENTE
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('emisor', 'receptor')
        ordering = ['-fecha_solicitud']
        verbose_name = 'Amistad'
        verbose_name_plural = 'Amistades'

    def __str__(self):
        return f"{self.emisor.nombre} → {self.receptor.nombre} ({self.estado})"

    @classmethod
    def son_amigos(cls, usuario1, usuario2):
        """Verifica si dos usuarios son amigos"""
        return cls.objects.filter(
            models.Q(emisor=usuario1, receptor=usuario2, estado=cls.ACEPTADA) |
            models.Q(emisor=usuario2, receptor=usuario1, estado=cls.ACEPTADA)
        ).exists()

    @classmethod
    def solicitud_existe(cls, usuario1, usuario2):
        """Verifica si existe una solicitud pendiente entre dos usuarios"""
        return cls.objects.filter(
            models.Q(emisor=usuario1, receptor=usuario2, estado=cls.PENDIENTE) |
            models.Q(emisor=usuario2, receptor=usuario1, estado=cls.PENDIENTE)
        ).exists()

    @classmethod
    def obtener_amigos(cls, usuario):
        """Obtiene todos los amigos de un usuario"""
        amistades = cls.objects.filter(
            models.Q(emisor=usuario, estado=cls.ACEPTADA) |
            models.Q(receptor=usuario, estado=cls.ACEPTADA)
        )
        
        amigos = []
        for amistad in amistades:
            if amistad.emisor == usuario:
                amigos.append(amistad.receptor)
            else:
                amigos.append(amistad.emisor)
        
        return amigos   