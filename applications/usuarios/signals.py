# applications/usuarios/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Usuario

@receiver(post_save, sender=User)
def crear_usuario_automatico(sender, instance, created, **kwargs):
    """Crea un Usuario automáticamente cuando se crea un User"""
    if created:
        # Solo crear si no existe
        if not hasattr(instance, 'usuario'):
            Usuario.objects.create(
                user=instance,
                tipo='aprendiz',  # Tipo por defecto
                documento='temp_' + str(instance.id),
                nombre=instance.username,
                email=instance.email or f'{instance.username}@temp.com'
            )