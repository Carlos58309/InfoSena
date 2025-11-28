from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_chats, name="lista_chats"),
    path("<int:usuario_id>/", views.ver_chat, name="ver_chat"),
]
