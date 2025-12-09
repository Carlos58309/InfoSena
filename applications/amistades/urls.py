# applications/amistades/urls.py

from django.urls import path
from . import views

app_name = 'amistades'

urlpatterns = [
    path('enviar/<int:usuario_id>/', views.enviar_solicitud, name='enviar_solicitud'),
    path('cancelar/<int:usuario_id>/', views.cancelar_solicitud, name='cancelar_solicitud'),
    path('aceptar/<int:solicitud_id>/', views.aceptar_solicitud, name='aceptar_solicitud'),
    path('rechazar/<int:solicitud_id>/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('eliminar/<int:usuario_id>/', views.eliminar_amigo, name='eliminar_amigo'),
]