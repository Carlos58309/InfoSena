from django.db import models
from applications.registro.models import Bienestar
from django.contrib.auth.models import User
from django.conf import settings

class Publicacion(models.Model):
    CATEGORIA_CHOICES = [
        ('salud', 'Salud'),
        ('bienestar', 'Bienestar'),
        ('evento', 'Evento'),
        ('informacion', 'Información General'),
        ('otro', 'Otro'),
    ]
    
    # IMPORTANTE: El campo debe ser ForeignKey
    autor = models.ForeignKey(
        Bienestar, 
        on_delete=models.CASCADE, 
        related_name='publicaciones'
    )
    
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='informacion')
    imagen = models.ImageField(upload_to='publicaciones/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
    
    def __str__(self):
        return f"{self.titulo} - {self.autor.nombre}"
    
    def total_likes(self):
        return self.likes.count()
    
class Like(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'publicacion')  # 🔥 evita likes duplicados

class Comentario(models.Model):
    publicacion = models.ForeignKey(
        'Publicacion',
        related_name='comentarios',
        on_delete=models.CASCADE
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.autor} - {self.contenido[:20]}'