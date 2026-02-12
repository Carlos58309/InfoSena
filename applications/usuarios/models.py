# applications/usuarios/models.py

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
    documento = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    foto = models.ImageField(upload_to='perfils/', null=True, blank=True)
    es_admin = models.BooleanField(default=False)
    class Meta:
        db_table = 'usuario_unificado'

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    # ====================
    # PROPIEDADES DINÁMICAS
    # ====================
    def get_perfil_completo(self):
        """Obtiene el perfil completo desde la tabla original"""
        from applications.registro.models import Aprendiz, Instructor, Bienestar
        
        try:
            if self.tipo == 'aprendiz':
                return Aprendiz.objects.get(numero_documento=self.documento)
            elif self.tipo == 'instructor':
                return Instructor.objects.get(numero_documento=self.documento)
            elif self.tipo == 'bienestar':
                return Bienestar.objects.get(numero_documento=self.documento)
        except Exception:
            return None

    @property
    def numero_documento(self):
        """Obtiene el número de documento"""
        return self.documento

    @property
    def tipo_documento(self):
        """Obtiene el tipo de documento desde la tabla original"""
        perfil = self.get_perfil_completo()
        return perfil.tipo_documento if perfil else "No especificado"

    @property
    def centro_formativo(self):
        """Obtiene el centro formativo desde la tabla original"""
        perfil = self.get_perfil_completo()
        return perfil.centro_formativo if perfil else "No especificado"

    @property
    def region(self):
        """Obtiene la región desde la tabla original"""
        perfil = self.get_perfil_completo()
        return perfil.region if perfil else "No especificada"

    @property
    def ficha(self):
        """Obtiene la ficha (solo aprendices)"""
        if self.tipo == 'aprendiz':
            perfil = self.get_perfil_completo()
            return perfil.ficha if perfil else "No especificada"
        return None

    @property
    def jornada(self):
        """Obtiene la jornada (solo aprendices)"""
        if self.tipo == 'aprendiz':
            perfil = self.get_perfil_completo()
            return perfil.jornada if perfil else "No especificada"
        return None

    @property
    def tipo_perfil(self):
        """Alias para compatibilidad"""
        return self.tipo

    def get_tipo_perfil_display(self):
        """Retorna el tipo de perfil en formato legible"""
        tipos = {
            'aprendiz': 'Aprendiz',
            'instructor': 'Instructor',
            'bienestar': 'Bienestar al Aprendiz'
        }
        return tipos.get(self.tipo, self.tipo.capitalize())