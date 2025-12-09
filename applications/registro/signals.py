from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
from django.contrib.auth.models import User

# ======================================
#  CREAR AUTOMÁTICAMENTE UN USUARIO
# ======================================
@receiver(post_save, sender=Aprendiz)
def crear_usuario_aprendiz(sender, instance, created, **kwargs):
    if created:
        user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password=instance.contrasena
        )
        Usuario.objects.create(
            user=user, 
            tipo="aprendiz",
            documento=instance.numero_documento,
            nombre=instance.nombre,
            email=instance.email,
            foto=instance.foto if instance.foto else None
        )
    else:
        # Actualizar foto si el registro fue modificado
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            if instance.foto:
                usuario.foto = instance.foto
                usuario.save()
        except Usuario.DoesNotExist:
            pass


@receiver(post_save, sender=Instructor)
def crear_usuario_instructor(sender, instance, created, **kwargs):
    if created:
        user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password=instance.contrasena
        )
        Usuario.objects.create(
            user=user, 
            tipo="instructor",
            documento=instance.numero_documento,
            nombre=instance.nombre,
            email=instance.email,
            foto=instance.foto if instance.foto else None
        )
    else:
        # Actualizar foto si el registro fue modificado
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            if instance.foto:
                usuario.foto = instance.foto
                usuario.save()
        except Usuario.DoesNotExist:
            pass


@receiver(post_save, sender=Bienestar)
def crear_usuario_bienestar(sender, instance, created, **kwargs):
    if created:
        user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password=instance.contrasena
        )
        Usuario.objects.create(
            user=user, 
            tipo="bienestar",
            documento=instance.numero_documento,
            nombre=instance.nombre,
            email=instance.email,
            foto=instance.foto if instance.foto else None
        )
    else:
        # Actualizar foto si el registro fue modificado
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            if instance.foto:
                usuario.foto = instance.foto
                usuario.save()
        except Usuario.DoesNotExist:
            pass


# ======================================
#  ELIMINAR USUARIO AL ELIMINAR REGISTRO
# ======================================
@receiver(post_delete, sender=Aprendiz)
def eliminar_usuario_aprendiz(sender, instance, **kwargs):
    Usuario.objects.filter(documento=instance.numero_documento).delete()


@receiver(post_delete, sender=Instructor)
def eliminar_usuario_instructor(sender, instance, **kwargs):
    Usuario.objects.filter(documento=instance.numero_documento).delete()


@receiver(post_delete, sender=Bienestar)
def eliminar_usuario_bienestar(sender, instance, **kwargs):
    Usuario.objects.filter(documento=instance.numero_documento).delete()
