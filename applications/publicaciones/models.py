from django.db import models
from applications.registro.models import Bienestar

class Publicacion(models.Model):
    """
    Modelo de Publicación - CORREGIDO para usar Bienestar directamente
    """
    CATEGORIA_CHOICES = [
        ('salud', 'Salud'),
        ('bienestar', 'Bienestar'),
        ('evento', 'Evento'),
        ('informacion', 'Información General'),
        ('otro', 'Otro'),
    ]
    
    # Campo autor usando Bienestar DIRECTAMENTE
    autor = models.ForeignKey(
        Bienestar,
        on_delete=models.CASCADE,
        related_name='publicaciones'
    )
    
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='informacion')
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
    
    def total_comentarios(self):
        return self.comentarios.count()


class ArchivoPublicacion(models.Model):
    """
    Modelo para almacenar múltiples imágenes y videos por publicación
    """
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('video', 'Video'),
    ]
    
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='archivos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to='publicaciones/%Y/%m/%d/')
    orden = models.PositiveIntegerField(default=0)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['orden', 'fecha_subida']
        verbose_name = 'Archivo de Publicación'
        verbose_name_plural = 'Archivos de Publicaciones'
    
    def __str__(self):
        return f"{self.tipo} - {self.publicacion.titulo}"
    
    def es_imagen(self):
        extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return any(self.archivo.name.lower().endswith(ext) for ext in extensiones_imagen)
    
    def es_video(self):
        extensiones_video = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        return any(self.archivo.name.lower().endswith(ext) for ext in extensiones_video)


class Like(models.Model):
    """
    Sistema de likes - usando Bienestar
    """
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    usuario = models.ForeignKey(
        Bienestar,
        on_delete=models.CASCADE
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'publicacion')
        verbose_name = 'Me gusta'
        verbose_name_plural = 'Me gusta'
    
    def __str__(self):
        return f"{self.usuario.nombre} - {self.publicacion.titulo}"


class Comentario(models.Model):
    """
    Sistema de comentarios - usando Bienestar
    """
    publicacion = models.ForeignKey(
        Publicacion,
        related_name='comentarios',
        on_delete=models.CASCADE
    )
    autor = models.ForeignKey(
        Bienestar,
        on_delete=models.CASCADE
    )
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fecha_creacion']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'{self.autor.nombre} - {self.contenido[:20]}'