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

    # Asegurar que el usuario tenga perfil
    usuario, created = Usuario.objects.get_or_create(user=request.user)

    chats = Chat.objects.filter(participantes=usuario)

    return render(request, 'lista_chats.html', {'chats': chats})


@login_required
def ver_chat(request, usuario_id):
    yo = get_object_or_404(Usuario, email=request.user.email)
    otro = get_object_or_404(Usuario, id=usuario_id)

    # Buscar si ya hay chat
    chat = Chat.objects.filter(participantes=yo).filter(participantes=otro).first()

    if not chat:
        chat = Chat.objects.create()
        chat.participantes.add(yo, otro)

    if request.method == "POST":
        contenido = request.POST.get("mensaje")
        if contenido:
            Mensaje.objects.create(
                chat=chat,
                autor=yo,
                contenido=contenido
            )
        return redirect("chat:ver_chat", usuario_id=otro.id)

    mensajes = Mensaje.objects.filter(chat=chat).order_by("enviado")

    return render(request, "chat.html", {
        "chat": chat,
        "mensajes": mensajes,
        "otro": otro,
        "yo": yo,
    })
