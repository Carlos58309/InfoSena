## applications/perfil/models.py
## AGREGAR este modelo al archivo models.py de la app perfil

from django.db import models


class PrivacidadPerfil(models.Model):
    """
    Guarda qué campos del perfil son visibles públicamente.
    Un registro por usuario (identificado por numero_documento).
    Si no existe registro → todo visible (comportamiento por defecto).
    """
    numero_documento = models.CharField(max_length=30, unique=True, db_index=True)

    # Campos que se pueden ocultar
    mostrar_email          = models.BooleanField(default=True)
    mostrar_documento      = models.BooleanField(default=True)
    mostrar_centro         = models.BooleanField(default=True)
    mostrar_region         = models.BooleanField(default=True)
    mostrar_ficha          = models.BooleanField(default=True)   # solo aprendices
    mostrar_jornada        = models.BooleanField(default=True)   # solo aprendices

    class Meta:
        verbose_name = 'Privacidad de perfil'
        verbose_name_plural = 'Privacidades de perfil'

    def __str__(self):
        return f'Privacidad de {self.numero_documento}'

    @classmethod
    def obtener_o_crear(cls, numero_documento):
        obj, _ = cls.objects.get_or_create(numero_documento=str(numero_documento))
        return obj