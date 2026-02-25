# edicion
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from applications.registro.models import Bienestar

class Publicacion(models.Model):
    # ... todo igual que antes, no tocar ...
    CATEGORIA_CHOICES = [
        ('salud', 'Salud'),
        ('bienestar', 'Bienestar'),
        ('evento', 'Evento'),
        ('informacion', 'Información General'),
        ('otro', 'Otro'),
    ]
    autor = models.ForeignKey(Bienestar, on_delete=models.CASCADE, related_name='publicaciones')
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
    # ... igual que antes, no tocar ...
    TIPO_CHOICES = [('imagen', 'Imagen'), ('video', 'Video')]
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='archivos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to='publicaciones/%Y/%m/%d/')
    orden = models.PositiveIntegerField(default=0)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'fecha_subida']

    def __str__(self):
        return f"{self.tipo} - {self.publicacion.titulo}"

    def es_imagen(self):
        return any(self.archivo.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'])

    def es_video(self):
        return any(self.archivo.name.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'])


# ✅ LIKE GENÉRICO — funciona con Aprendiz, Instructor y Bienestar
class Like(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='likes')
    
    # Tipo de usuario (aprendiz, instructor, bienestar)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=20)  # numero_documento es CharField
    usuario = GenericForeignKey('content_type', 'object_id')
    
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('publicacion', 'content_type', 'object_id')
        verbose_name = 'Me gusta'
        verbose_name_plural = 'Me gusta'

    def __str__(self):
        return f"Like en {self.publicacion.titulo}"


# ✅ COMENTARIO GENÉRICO — funciona con Aprendiz, Instructor y Bienestar
class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=20)
    autor = GenericForeignKey('content_type', 'object_id')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_creacion']

    def __str__(self):
        return f'Comentario en {self.publicacion.titulo}'

    def get_autor_nombre(self):
        try:
            from applications.registro.models import Aprendiz, Instructor, Bienestar
            modelo = self.content_type.model_class()
            obj = modelo.objects.get(numero_documento=self.object_id)
            return obj.nombre
        except Exception:
            return 'Usuario desconocido'

    def get_autor_foto(self):
        try:
            from applications.registro.models import Aprendiz, Instructor, Bienestar
            modelo = self.content_type.model_class()
            obj = modelo.objects.get(numero_documento=self.object_id)
            if obj.foto:
                return obj.foto.url
            return None
        except Exception:
            return None
    def get_autor_foto(self):
        if self.autor and self.autor.foto:
            return self.autor.foto.url
        return None