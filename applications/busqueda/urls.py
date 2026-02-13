# applications/busqueda/urls.py

from django.urls import path
from . import views

app_name = 'busqueda'

urlpatterns = [
    # API de búsqueda
    path('usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
    
    # Historial
    path('historial/', views.obtener_historial, name='obtener_historial'),
    path('guardar/', views.guardar_en_historial, name='guardar_historial'),
    path('eliminar/', views.eliminar_del_historial, name='eliminar_historial'),
    path('limpiar/', views.limpiar_historial, name='limpiar_historial'),
    
    # ✅ NUEVA: Obtener documento del usuario
    path('obtener-documento/<int:usuario_id>/', views.obtener_documento_usuario, name='obtener_documento'),
]