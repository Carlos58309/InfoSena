# applications/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer de WebSocket para el chat en tiempo real
    """
    
    async def connect(self):
        """
        Ejecutado cuando un cliente se conecta
        """
        # Obtener ID del chat desde la URL
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        
        # Obtener usuario
        self.user = self.scope.get('user')
        
        # Verificar que el usuario tiene acceso al chat
        tiene_acceso = await self.verificar_acceso_chat()
        
        if not tiene_acceso:
            await self.close()
            return
        
        # Unirse al grupo del chat
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        # Aceptar conexión
        await self.accept()
        
        print(f"✅ Usuario {self.user.id} conectado al chat {self.chat_id}")
    
    async def disconnect(self, close_code):
        """
        Ejecutado cuando un cliente se desconecta
        """
        # Salir del grupo del chat
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
        
        print(f"❌ Usuario {self.user.id} desconectado del chat {self.chat_id}")
    
    async def receive(self, text_data):
        """
        Ejecutado cuando se recibe un mensaje del cliente
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'send_message':
                await self.handle_send_message(data)
            elif action == 'typing':
                await self.handle_typing(data)
            elif action == 'mark_as_read':
                await self.handle_mark_as_read(data)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Formato JSON inválido'
            }))
    
    async def handle_send_message(self, data):
        """
        Maneja el envío de un nuevo mensaje
        """
        contenido = data.get('contenido', '').strip()
        
        if not contenido:
            return
        
        # Guardar mensaje en la base de datos
        mensaje = await self.guardar_mensaje(contenido)
        
        if not mensaje:
            return
        
        # Enviar mensaje a todos en el grupo
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'mensaje': {
                    'id': mensaje['id'],
                    'autor_id': mensaje['autor_id'],
                    'autor_nombre': mensaje['autor_nombre'],
                    'autor_foto': mensaje['autor_foto'],
                    'contenido': mensaje['contenido'],
                    'enviado': mensaje['enviado'],
                    'tiempo_transcurrido': mensaje['tiempo_transcurrido'],
                }
            }
        )
    
    async def handle_typing(self, data):
        """
        Maneja el evento de "usuario está escribiendo"
        """
        is_typing = data.get('is_typing', False)
        
        # Enviar notificación de typing a todos menos al emisor
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'user_nombre': await self.obtener_nombre_usuario(),
                'is_typing': is_typing,
            }
        )
    
    async def handle_mark_as_read(self, data):
        """
        Marca mensajes como leídos
        """
        mensaje_ids = data.get('mensaje_ids', [])
        
        if mensaje_ids:
            await self.marcar_mensajes_como_leidos(mensaje_ids)
    
    # ==========================================
    # HANDLERS DE EVENTOS
    # ==========================================
    
    async def chat_message(self, event):
        """
        Maneja eventos de tipo 'chat_message' del grupo
        """
        # Enviar mensaje al WebSocket del cliente
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'mensaje': event['mensaje']
        }))
    
    async def user_typing(self, event):
        """
        Maneja eventos de tipo 'user_typing' del grupo
        """
        # No enviar al usuario que está escribiendo
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_nombre': event['user_nombre'],
                'is_typing': event['is_typing'],
            }))
    
    # ==========================================
    # MÉTODOS DE BASE DE DATOS
    # ==========================================
    
    @database_sync_to_async
    def verificar_acceso_chat(self):
        """
        Verifica que el usuario tiene acceso al chat
        """
        from applications.chat.models import Chat
        
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return chat.participantes.filter(id=self.user.id).exists()
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def guardar_mensaje(self, contenido):
        """
        Guarda un mensaje en la base de datos
        """
        from applications.chat.models import Chat, Mensaje
        from applications.usuarios.models import Usuario
        
        try:
            chat = Chat.objects.get(id=self.chat_id)
            usuario = Usuario.objects.get(id=self.user.id)
            
            mensaje = Mensaje.objects.create(
                chat=chat,
                autor=usuario,
                contenido=contenido
            )
            
            # Actualizar timestamp del chat
            chat.actualizado_en = timezone.now()
            chat.save(update_fields=['actualizado_en'])
            
            return {
                'id': mensaje.id,
                'autor_id': usuario.id,
                'autor_nombre': usuario.nombre,
                'autor_foto': usuario.foto.url if usuario.foto else None,
                'contenido': mensaje.contenido,
                'enviado': mensaje.enviado.isoformat(),
                'tiempo_transcurrido': mensaje.tiempo_transcurrido(),
            }
        
        except (Chat.DoesNotExist, Usuario.DoesNotExist):
            return None
    
    @database_sync_to_async
    def obtener_nombre_usuario(self):
        """
        Obtiene el nombre del usuario actual
        """
        from applications.usuarios.models import Usuario
        
        try:
            usuario = Usuario.objects.get(id=self.user.id)
            return usuario.nombre
        except Usuario.DoesNotExist:
            return "Usuario"
    
    @database_sync_to_async
    def marcar_mensajes_como_leidos(self, mensaje_ids):
        """
        Marca mensajes como leídos
        """
        from applications.chat.models import Mensaje
        
        mensajes = Mensaje.objects.filter(
            id__in=mensaje_ids,
            chat_id=self.chat_id
        ).exclude(autor_id=self.user.id)
        
        for mensaje in mensajes:
            mensaje.marcar_como_visto()