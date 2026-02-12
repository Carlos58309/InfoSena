# =====================================================
# OPCIÓN A: INTEGRAR EN applications/sesion/urls.py
# =====================================================
# Recomendado si ya tienes path("chat/", chat_view, name="chat")
# y quieres mantener la misma estructura de URLs

from django.urls import path
from . import views

# Importar vistas del chat
from applications.chat import views as chat_views

app_name = 'chat'

urlpatterns = [
    path("chat/", chat_views.lista_chats, name="lista_chats"),  # ✅ Nueva vista de lista
    path("chat/room/<int:chat_id>/", chat_views.chat_room, name="chat_room"),
    path("chat/iniciar/<int:usuario_id>/", chat_views.iniciar_chat, name="iniciar_chat"),
    path("chat/enviar/<int:chat_id>/", chat_views.enviar_mensaje, name="enviar_mensaje"),
    path("chat/crear-grupo/", chat_views.crear_grupo, name="crear_grupo"),
    
    # API endpoints para AJAX
    path("chat/api/mensajes/<int:chat_id>/", chat_views.api_obtener_mensajes, name="api_obtener_mensajes"),
    path("chat/api/enviar/<int:chat_id>/", chat_views.api_enviar_mensaje, name="api_enviar_mensaje"),
]


