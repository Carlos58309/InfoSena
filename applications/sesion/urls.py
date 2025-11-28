from django.urls import path
from .views import login_view, dashboard_view, amigos_view

app_name = "sesion"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("home/", dashboard_view, name="home"),
    path("amigos/", amigos_view, name="amigos"),
]

