

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from applications.usuarios.models import Usuario
from applications.mensaje.models import Mensaje
from .models import Chat
from django.contrib.auth.models import User

@login_required
def lista_chats(request):
    """Mostrar todos los chats del usuario."""
    usuario = request.user

    chats = Chat.objects.filter(user1=usuario) | Chat.objects.filter(user2=usuario)

    return render(request, "chat.html", {
        "chats": chats,
    })


@login_required
def ver_chat(request, user_id):
    """Abrir un chat con un usuario."""
    usuario = request.user
    receptor = get_object_or_404(User, id=user_id)

    # Verificar si el chat existe
    chat = Chat.objects.filter(
        user1=usuario, user2=receptor
    ).first() or Chat.objects.filter(
        user1=receptor, user2=usuario
    ).first()

    # Si no existe, se crea
    if not chat:
        chat = Chat.objects.create(user1=usuario, user2=receptor)

    # Enviar mensaje
    if request.method == "POST":
        mensaje = request.POST.get("mensaje")
        if mensaje:
            Mensaje.objects.create(
                chat=chat,
                sender=usuario,
                text=mensaje
            )
        return redirect("ver_chat", user_id=receptor.id)

    mensajes = Mensaje.objects.filter(chat=chat)

    return render(request, "chat.html", {
        "chat": chat,
        "mensajes": mensajes,
        "receptor": receptor,
    })
