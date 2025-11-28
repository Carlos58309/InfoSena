from django.db import models
from applications.usuarios.models import Usuario
from applications.chat.models import Chat

class Mensaje(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensajes")
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    contenido = models.TextField()
    enviado = models.DateTimeField(auto_now_add=True)
    visto = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje {self.id} en chat {self.chat.id}"

