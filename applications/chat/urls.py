from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.lista_chats, name="lista_chats"),
    path("<int:usuario_id>/", views.ver_chat, name="ver_chat"),
]
