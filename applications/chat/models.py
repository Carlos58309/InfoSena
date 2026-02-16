# applications/chat/models.py
from django.db import models
from django.utils import timezone
from applications.usuarios.models import Usuario


class Chat(models.Model):
    """
    Modelo de Chat - Puede ser individual o grupal
    """
    # Participantes del chat
    participantes = models.ManyToManyField(
        Usuario, 
        related_name='chats',
        verbose_name='Participantes'
    )
    
    # Para chats grupales
    is_group = models.BooleanField(default=False, verbose_name='Es grupo')
    nombre_grupo = models.CharField(max_length=100, blank=True, null=True)
    descripcion_grupo = models.TextField(blank=True, null=True)
    foto_grupo = models.ImageField(upload_to='grupos/', blank=True, null=True)
    admin_grupo = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='grupos_admin'
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats'
        ordering = ['-actualizado_en']
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
    
    def __str__(self):
        if self.is_group:
            return f"Grupo: {self.nombre_grupo}"
        else:
            participantes = self.participantes.all()[:2]
            nombres = " y ".join([p.nombre for p in participantes])
            return f"Chat: {nombres}"
    
    def obtener_nombre_para_usuario(self, usuario):
        """Obtiene el nombre del chat desde la perspectiva de un usuario"""
        if self.is_group:
            return self.nombre_grupo
        else:
            otro = self.participantes.exclude(id=usuario.id).first()
            return otro.nombre if otro else "Chat"
    
    def obtener_foto_para_usuario(self, usuario):
        """Obtiene la foto del chat desde la perspectiva de un usuario"""
        if self.is_group:
            return self.foto_grupo.url if self.foto_grupo else None
        else:
            otro = self.participantes.exclude(id=usuario.id).first()
            return otro.foto.url if otro and otro.foto else None
    
    def ultimo_mensaje(self):
        """Obtiene el último mensaje del chat"""
        return self.mensajes.order_by('-enviado').first()
    
    def mensajes_no_leidos_para_usuario(self, usuario):
        """Cuenta mensajes no leídos para un usuario específico"""
        return self.mensajes.filter(visto=False).exclude(autor=usuario).count()
    
    @classmethod
    def obtener_o_crear_chat_individual(cls, usuario1, usuario2):
        """
        Obtiene o crea un chat individual entre dos usuarios
        """
        # Buscar chat existente
        chat = cls.objects.filter(
            is_group=False,
            participantes=usuario1
        ).filter(
            participantes=usuario2
        ).first()
        
        # Si no existe, crear uno nuevo
        if not chat:
            chat = cls.objects.create(is_group=False)
            chat.participantes.add(usuario1, usuario2)
        
        return chat
    
    @classmethod
    def crear_grupo(cls, nombre, admin, participantes_ids, descripcion=None):
        """
        Crea un nuevo chat grupal
        """
        grupo = cls.objects.create(
            is_group=True,
            nombre_grupo=nombre,
            descripcion_grupo=descripcion,
            admin_grupo=admin
        )
        
        # Agregar admin
        grupo.participantes.add(admin)
        
        # Agregar otros participantes
        if participantes_ids:
            usuarios = Usuario.objects.filter(id__in=participantes_ids)
            grupo.participantes.add(*usuarios)
        
        return grupo
    
    

class Mensaje(models.Model):
    """
    Modelo de Mensaje
    """
    chat = models.ForeignKey(
        Chat, 
        on_delete=models.CASCADE, 
        related_name='mensajes'
    )
    autor = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    contenido = models.TextField()
    
    # Metadatos
    enviado = models.DateTimeField(auto_now_add=True)
    editado = models.DateTimeField(null=True, blank=True)
    visto = models.BooleanField(default=False)
    visto_en = models.DateTimeField(null=True, blank=True)
    
    # Archivos adjuntos (opcional)
    archivo = models.FileField(upload_to='mensajes/', blank=True, null=True)
    tipo_archivo = models.CharField(max_length=20, blank=True, null=True)  # imagen, documento, etc.
    
    class Meta:
        db_table = 'mensajes'
        ordering = ['enviado']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
    
    def __str__(self):
        preview = self.contenido[:50] + "..." if len(self.contenido) > 50 else self.contenido
        return f"{self.autor.nombre}: {preview}"
    
    def marcar_como_visto(self):
        """Marca el mensaje como visto"""
        if not self.visto:
            self.visto = True
            self.visto_en = timezone.now()
            self.save(update_fields=['visto', 'visto_en'])
    
    def tiempo_transcurrido(self):
        """Retorna tiempo transcurrido en formato legible"""
        ahora = timezone.now()
        diferencia = ahora - self.enviado
        
        segundos = diferencia.total_seconds()
        
        if segundos < 60:
            return "Ahora"
        elif segundos < 3600:
            minutos = int(segundos / 60)
            return f"Hace {minutos} min"
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f"Hace {horas}h"
        else:
            dias = int(segundos / 86400)
            return f"Hace {dias}d"


class MensajeVisto(models.Model):
    """
    Registro de quién ha visto cada mensaje (para grupos)
    """
    mensaje = models.ForeignKey(
        Mensaje,
        on_delete=models.CASCADE,
        related_name='vistos_por'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )
    visto_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mensajes_vistos'
        unique_together = ('mensaje', 'usuario')
        verbose_name = 'Mensaje Visto'
        verbose_name_plural = 'Mensajes Vistos'
    
    def __str__(self):
        return f"{self.usuario.nombre} vio mensaje {self.mensaje.id}"