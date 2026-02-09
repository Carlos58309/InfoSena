# applications/busqueda/urls.py

from django.urls import path
from . import views

app_name = 'busqueda'

urlpatterns = [
    path('usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
    path('guardar/', views.guardar_busqueda, name='guardar_busqueda'),
    path('historial/', views.obtener_historial, name='obtener_historial'),
    path('eliminar/', views.eliminar_busqueda, name='eliminar_busqueda'),
    path('limpiar/', views.limpiar_historial, name='limpiar_historial'),
]