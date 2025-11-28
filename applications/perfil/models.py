# perfil/models.py
from django.db import models
from django.contrib.auth.models import User

class Aprendiz(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='aprendiz_profile')
    ficha = models.CharField(max_length=50, blank=True, null=True)
    programa = models.CharField(max_length=100, blank=True, null=True)

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    especialidad = models.CharField(max_length=100, blank=True, null=True)

class Bienestar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bienestar_profile')
    area = models.CharField(max_length=100, blank=True, null=True)
