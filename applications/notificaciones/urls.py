# applications/notificaciones/urls.py

from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Vista principal de notificaciones
    path('', views.lista_notificaciones, name='lista'),
    
    # API para obtener notificaciones (usado por AJAX)
    path('api/obtener/', views.obtener_notificaciones, name='obtener_notificaciones'),
    
    # Marcar como leída una notificación específica
    path('marcar-leida/<int:notificacion_id>/', views.marcar_leida, name='marcar_leida'),
    
    # Marcar todas como leídas
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]