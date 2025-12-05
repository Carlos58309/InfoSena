from django.urls import path
from .views import *

app_name = "sesion"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("home/", dashboard_view, name="home"),
    path("amigos/", amigos_view, name="amigos"),
    path("chat/", chat_view, name="chat"),  # <-- ESTA LA AGREGAMOS
    path("perfil/", perfil_view, name="perfil"),  # <-- ESTA TAMBIÉN

]

