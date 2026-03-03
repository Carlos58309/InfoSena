# applications/chat/models.py
from django.db import models
from django.utils import timezone
from applications.usuarios.models import Usuario


class Chat(models.Model):
    participantes = models.ManyToManyField(
        Usuario,
        related_name='chats',
        verbose_name='Participantes'
    )

    # Grupales
    is_group = models.BooleanField(default=False, verbose_name='Es grupo')
    nombre_grupo = models.CharField(max_length=100, blank=True, null=True)
    descripcion_grupo = models.TextField(blank=True, null=True)
    foto_grupo = models.ImageField(upload_to='grupos/', blank=True, null=True)
    admin_grupo = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='grupos_admin'
    )

    # Usuarios que "vaciaron" este chat — solo les desaparece a ellos
    vaciado_para = models.ManyToManyField(
        Usuario,
        blank=True,
        related_name='chats_vaciados',
        verbose_name='Vaciado para'
    )
    # Timestamp del vaciado por usuario (guardamos en MensajeEliminadoParaUsuario)

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
        participantes = self.participantes.all()[:2]
        nombres = " y ".join([p.nombre for p in participantes])
        return f"Chat: {nombres}"

    def obtener_nombre_para_usuario(self, usuario):
        if self.is_group:
            return self.nombre_grupo
        otro = self.participantes.exclude(id=usuario.id).first()
        return otro.nombre if otro else "Chat"

    def obtener_foto_para_usuario(self, usuario):
        if self.is_group:
            return self.foto_grupo.url if self.foto_grupo else None
        otro = self.participantes.exclude(id=usuario.id).first()
        return otro.foto.url if otro and otro.foto else None

    def ultimo_mensaje(self):
        return self.mensajes.order_by('-enviado').first()

    def ultimo_mensaje_para_usuario(self, usuario):
        """Ultimo mensaje visible para este usuario (respeta vaciado y eliminados)."""
        vaciado_en = ChatVaciadoPorUsuario.objects.filter(
            chat=self, usuario=usuario
        ).values_list('vaciado_en', flat=True).first()

        qs = self.mensajes.exclude(
            id__in=MensajeEliminadoParaUsuario.objects.filter(
                usuario=usuario
            ).values_list('mensaje_id', flat=True)
        )
        if vaciado_en:
            qs = qs.filter(enviado__gt=vaciado_en)

        return qs.order_by('-enviado').first()

    def mensajes_no_leidos_para_usuario(self, usuario):
        vaciado_en = ChatVaciadoPorUsuario.objects.filter(
            chat=self, usuario=usuario
        ).values_list('vaciado_en', flat=True).first()

        qs = self.mensajes.filter(visto=False).exclude(autor=usuario).exclude(
            id__in=MensajeEliminadoParaUsuario.objects.filter(
                usuario=usuario
            ).values_list('mensaje_id', flat=True)
        )
        if vaciado_en:
            qs = qs.filter(enviado__gt=vaciado_en)

        return qs.count()

    def mensajes_visibles_para_usuario(self, usuario):
        """QuerySet de mensajes que este usuario puede ver."""
        vaciado_en = ChatVaciadoPorUsuario.objects.filter(
            chat=self, usuario=usuario
        ).values_list('vaciado_en', flat=True).first()

        qs = self.mensajes.exclude(
            id__in=MensajeEliminadoParaUsuario.objects.filter(
                usuario=usuario
            ).values_list('mensaje_id', flat=True)
        )
        if vaciado_en:
            qs = qs.filter(enviado__gt=vaciado_en)

        return qs.select_related('autor').order_by('enviado')

    def vaciar_para_usuario(self, usuario):
        """Registra que el usuario vació el chat (solo le desaparece a él)."""
        ChatVaciadoPorUsuario.objects.update_or_create(
            chat=self,
            usuario=usuario,
            defaults={'vaciado_en': timezone.now()}
        )

    @classmethod
    def obtener_o_crear_chat_individual(cls, usuario1, usuario2):
        chat = cls.objects.filter(
            is_group=False,
            participantes=usuario1
        ).filter(participantes=usuario2).first()

        if not chat:
            chat = cls.objects.create(is_group=False)
            chat.participantes.add(usuario1, usuario2)
        return chat

    @classmethod
    def crear_grupo(cls, nombre, admin, participantes_ids, descripcion=None):
        grupo = cls.objects.create(
            is_group=True,
            nombre_grupo=nombre,
            descripcion_grupo=descripcion,
            admin_grupo=admin
        )
        grupo.participantes.add(admin)
        if participantes_ids:
            usuarios = Usuario.objects.filter(id__in=participantes_ids)
            grupo.participantes.add(*usuarios)
        return grupo


class ChatVaciadoPorUsuario(models.Model):
    """Registra cuándo un usuario vació un chat (los mensajes anteriores le quedan ocultos)."""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='vaciados_por')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='chats_vaciados_registros')
    vaciado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'chat_vaciado_por_usuario'
        unique_together = ('chat', 'usuario')
        verbose_name = 'Chat Vaciado por Usuario'


class Mensaje(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados')
    contenido = models.TextField()

    enviado = models.DateTimeField(auto_now_add=True)
    editado = models.DateTimeField(null=True, blank=True)
    visto = models.BooleanField(default=False)
    visto_en = models.DateTimeField(null=True, blank=True)

    # Archivos adjuntos
    archivo = models.FileField(upload_to='mensajes/', blank=True, null=True)
    tipo_archivo = models.CharField(max_length=20, blank=True, null=True)
    nombre_archivo = models.CharField(max_length=255, blank=True, default='')
    tamanio_archivo = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'mensajes'
        ordering = ['enviado']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        preview = self.contenido[:50] + "..." if len(self.contenido) > 50 else self.contenido
        return f"{self.autor.nombre}: {preview}"

    def marcar_como_visto(self):
        if not self.visto:
            self.visto = True
            self.visto_en = timezone.now()
            self.save(update_fields=['visto', 'visto_en'])

    def tiempo_transcurrido(self):
        ahora = timezone.now()
        segundos = (ahora - self.enviado).total_seconds()
        if segundos < 60:
            return "Ahora"
        elif segundos < 3600:
            return f"Hace {int(segundos / 60)} min"
        elif segundos < 86400:
            return f"Hace {int(segundos / 3600)}h"
        else:
            return f"Hace {int(segundos / 86400)}d"

    def puede_eliminar_para_todos(self, usuario):
        """
        Solo el autor puede eliminarlo para todos,
        y solo si fue enviado hace menos de 24 horas.
        """
        if self.autor != usuario:
            return False
        limite = timezone.now() - timezone.timedelta(hours=24)
        return self.enviado >= limite


class MensajeEliminadoParaUsuario(models.Model):
    """
    Registro de qué mensajes eliminó cada usuario para sí mismo.
    El mensaje sigue en la BD y otros participantes lo ven normalmente.
    """
    mensaje = models.ForeignKey(
        Mensaje,
        on_delete=models.CASCADE,
        related_name='eliminado_para'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mensajes_eliminados'
    )
    eliminado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensaje_eliminado_para_usuario'
        unique_together = ('mensaje', 'usuario')
        verbose_name = 'Mensaje Eliminado para Usuario'


class MensajeVisto(models.Model):
    mensaje = models.ForeignKey(Mensaje, on_delete=models.CASCADE, related_name='vistos_por')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    visto_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensajes_vistos'
        unique_together = ('mensaje', 'usuario')
        verbose_name = 'Mensaje Visto'
        verbose_name_plural = 'Mensajes Vistos'

    def __str__(self):
        return f"{self.usuario.nombre} vio mensaje {self.mensaje.id}"