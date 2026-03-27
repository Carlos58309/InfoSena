# registro/urls.py
from django.urls import path
from . import views

app_name = 'registro'

urlpatterns = [
    path('', views.registro_view, name='registro'),
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
    path('esperando-aprobacion/', views.esperando_aprobacion_view, name='esperando_aprobacion'),
    path('panel-aprobacion/', views.panel_aprobacion_view, name='panel_aprobacion'),
    path('rechazar-cuenta/', views.rechazar_cuenta_view, name='rechazar_cuenta'),
    path('aprobar-cuenta/', views.aprobar_cuenta_view, name='aprobar_cuenta'),
]