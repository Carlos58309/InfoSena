from django.db import models
from django.contrib.auth.models import User

class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    TIPO_USUARIO = (
        ('aprendiz', 'Aprendiz'),
        ('instructor', 'Instructor'),
        ('bienestar', 'Bienestar'),
    )

    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO)
    documento = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    foto = models.ImageField(upload_to='perfils/', null=True, blank=True)

    class Meta:
        db_table = 'usuario_unificado'

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"