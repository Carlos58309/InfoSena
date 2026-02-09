# applications/perfil/urls.py

from django.urls import path
from . import views

app_name = 'perfil'

urlpatterns = [
    # ========================================
    # URLS PRINCIPALES
    # ========================================
    
    # Perfil propio
    path('', views.perfiles, name='perfiles'),
    
    # Dashboard/Home
    path('home/', views.dashboard_view, name='home'),
    
    # Editar perfil
    path('editar/', views.editar_perfil, name='editar_perfil'),
    
    # Eliminar perfil
    path('eliminar/', views.eliminar_perfil, name='eliminar_perfil'),
    
    # ========================================
    # VER PERFIL DE OTROS USUARIOS
    # ========================================
    
    # ⚠️ IMPORTANTE: Esta URL debe estar AL FINAL
    # Ver perfil de cualquier usuario (por número de documento)
    path('ver/<str:documento>/', views.ver_perfil, name='ver_perfil'),
    
    # ❌ NO INCLUIR ESTA URL:
    # path('ver/<int:usuario_id>/', views.ver_perfil, name='ver_perfil'),
    # ↑ Esta es la que causaba el error
]