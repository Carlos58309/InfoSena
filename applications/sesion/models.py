from django.db import models
from django.utils import timezone
from applications.usuarios.models import Usuario
import random

class Sesion(models.Model):
    numero_documento = models.CharField(max_length=20)
    rol = models.CharField(
        max_length=50,
        choices=[
            ('Aprendiz', 'Aprendiz'),
            ('Instructor', 'Instructor'),
            ('Bienestar', 'Bienestar'),
        ]
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    exito = models.BooleanField(default=False)  # True si inició sesión correctamente

    class Meta:
        db_table = 'sesion'
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'

    def __str__(self):
        estado = "Exitosa" if self.exito else "Fallida"
        return f"{self.numero_documento} - {self.rol} ({estado})"

# 🔥 ESTE MODELO VA FUERA DE SESION
class CodigoRecuperacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.email} - {self.codigo}"

    @staticmethod
    def generar_codigo():
        return str(random.randint(100000, 999999))