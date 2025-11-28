from django.db import models
from applications.usuarios.models import Usuario

class Chat(models.Model):
    is_group = models.BooleanField(default=False)
    nombre_grupo = models.CharField(max_length=150, null=True, blank=True)
    participantes = models.ManyToManyField(Usuario, related_name="chats")
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {'grupo' if self.is_group else 'privado'} {self.id}"
