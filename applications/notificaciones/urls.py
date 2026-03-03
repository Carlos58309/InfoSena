# applications/notificaciones/urls.py
from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.lista_notificaciones, name='lista'),
    path('api/obtener/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('marcar-leida/<int:notificacion_id>/', views.marcar_leida, name='marcar_leida'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),

    # Nuevas
    path('api/silenciar-usuario/',    views.toggle_silenciar_usuario, name='toggle_silenciar_usuario'),
    path('api/verificar-silenciado/', views.verificar_silenciado,     name='verificar_silenciado'),
]