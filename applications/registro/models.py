# registro/models
from django.db import models


# ==========================
#  MODELO: Aprendiz
# ==========================
class Aprendiz(models.Model):
    numero_documento = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=150)
    tipo_documento = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    centro_formativo = models.CharField(max_length=150)
    region = models.CharField(max_length=100)
    jornada = models.CharField(max_length=50)
    ficha = models.CharField(max_length=50)
    contrasena = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='perfiles/aprendices/', null=True, blank=True)
    
    # NUEVOS CAMPOS PARA VERIFICACIÓN
    verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)
    codigo_expiracion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'aprendiz'
    
    def __str__(self):
        return f"{self.nombre} ({self.numero_documento})"


# ==========================
#  MODELO: Instructor
# ==========================
class Instructor(models.Model):
    numero_documento = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    region = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=20)
    centro_formativo = models.CharField(max_length=100)
    contrasena = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='perfiles/instructores/', null=True, blank=True)
    
    # NUEVOS CAMPOS PARA VERIFICACIÓN
    verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)
    codigo_expiracion = models.DateTimeField(blank=True, null=True)
    # NUEVO: Para verificación administrativa
    verificado_admin = models.BooleanField(default=False)
    codigo_admin = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        db_table = 'instructor'
    
    def __str__(self):
        return f"{self.nombre} ({self.numero_documento})"


# ==========================
#  MODELO: Bienestar
# ==========================
class Bienestar(models.Model):
    numero_documento = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=150)
    tipo_documento = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    centro_formativo = models.CharField(max_length=150, default="Centro desconocido")
    region = models.CharField(max_length=100)
    contrasena = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='perfiles/bienestar/', null=True, blank=True)
    
    # NUEVOS CAMPOS PARA VERIFICACIÓN
    verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)
    codigo_expiracion = models.DateTimeField(blank=True, null=True)
    # NUEVO: Para verificación administrativa
    verificado_admin = models.BooleanField(default=False)
    codigo_admin = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        db_table = 'bienestar'
    
    def __str__(self):
        return f"{self.nombre} ({self.numero_documento})"