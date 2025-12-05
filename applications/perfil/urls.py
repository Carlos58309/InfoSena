from django.urls import path
from . import views

app_name = 'perfil'

urlpatterns = [
    path('', views.perfil, name='perfiles'),
    path('home/', views.dashboard_view, name='home'),
    path('editar/', views.editar_perfil, name='editar_perfil'),
    path('eliminar/', views.eliminar_perfil, name='eliminar_perfil'),
]