# sesion/urls.py
from django.urls import path
from .views import *

app_name = "sesion"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("verificar-sesion/", verificar_sesion, name="verificar_sesion"),
    path("home/", home_view, name="home"),
    path("amigos/", amigos_view, name="amigos"),
    path("solicitar-correo/", solicitar_correo, name="solicitar_correo"),
    path("chat/", chat_view, name="chat"),  # <-- ESTA LA AGREGAMOS
    path("perfil/", perfil_view, name="perfil"),  # <-- ESTA TAMBIÉN
    path('', home, name='index'),
    path("verificar-codigo/", verificar_codigo, name="verificar_codigo"),
    path("nueva-contrasena/", nueva_contrasena, name="nueva_contrasena"),
]

