# applications/moderacion/models.py
"""
Modelos para registrar moderaciones y mantener historial
"""

from django.db import models
from applications.usuarios.models import Usuario


class RegistroModeracion(models.Model):
    """
    Registro de todas las moderaciones realizadas
    """
    TIPO_CONTENIDO_CHOICES = [
        ('texto', 'Texto'),
        ('imagen', 'Imagen'),
        ('video', 'Video'),
        ('archivo', 'Archivo'),
    ]
    
    RESULTADO_CHOICES = [
        ('aprobado', 'Aprobado'),
        ('bloqueado', 'Bloqueado'),
        ('error', 'Error'),
    ]
    
    # Metadatos de la moderación
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderaciones'
    )
    tipo_contenido = models.CharField(max_length=20, choices=TIPO_CONTENIDO_CHOICES)
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES)
    
    # Contenido moderado
    contenido_texto = models.TextField(blank=True, null=True)
    archivo_url = models.URLField(blank=True, null=True)
    
    # Resultado de la moderación
    razon = models.TextField()
    categorias_violadas = models.JSONField(default=list, blank=True)
    score_confianza = models.JSONField(default=dict, blank=True)
    metodo_usado = models.CharField(max_length=50, default='openai_api')
    
    # Contexto adicional
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'registros_moderacion'
        ordering = ['-creado_en']
        verbose_name = 'Registro de Moderación'
        verbose_name_plural = 'Registros de Moderación'
        indexes = [
            models.Index(fields=['-creado_en']),
            models.Index(fields=['usuario', '-creado_en']),
            models.Index(fields=['resultado']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.nombre if self.usuario else 'Anónimo'
        return f"{usuario_str} - {self.tipo_contenido} - {self.resultado}"


class UsuarioSancionado(models.Model):
    """
    Usuarios con sanciones por contenido inapropiado
    """
    TIPO_SANCION_CHOICES = [
        ('advertencia', 'Advertencia'),
        ('suspension_temporal', 'Suspensión Temporal'),
        ('baneo_permanente', 'Baneo Permanente'),
    ]
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sanciones'
    )
    tipo_sancion = models.CharField(max_length=30, choices=TIPO_SANCION_CHOICES)
    razon = models.TextField()
    
    # Duración de la sanción
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)  # Null = permanente
    
    # Sanción activa
    activa = models.BooleanField(default=True)
    
    # Moderador que aplicó la sanción
    aplicada_por = models.CharField(max_length=100, default='sistema_automatico')
    
    class Meta:
        db_table = 'usuarios_sancionados'
        ordering = ['-fecha_inicio']
        verbose_name = 'Usuario Sancionado'
        verbose_name_plural = 'Usuarios Sancionados'
    
    def __str__(self):
        return f"{self.usuario.nombre} - {self.tipo_sancion}"


class PalabraProhibida(models.Model):
    """
    Lista personalizable de palabras prohibidas
    """
    palabra = models.CharField(max_length=100, unique=True)
    severidad = models.IntegerField(
        default=1,
        help_text="1=Leve, 2=Moderado, 3=Severo, 4=Crítico"
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'palabras_prohibidas'
        ordering = ['-severidad', 'palabra']
        verbose_name = 'Palabra Prohibida'
        verbose_name_plural = 'Palabras Prohibidas'
    
    def __str__(self):
        return f"{self.palabra} (Severidad: {self.severidad})"