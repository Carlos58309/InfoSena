from django.urls import path
from . import views

app_name = 'publicaciones'

urlpatterns = [
    path('crear/', views.crear_publicacion, name='crear_publicacion'),
    path('listar/', views.listar_publicaciones, name='listar_publicaciones'),
    path('mis-publicaciones/', views.mis_publicaciones, name='mis_publicaciones'),
    path('ver/<int:publicacion_id>/', views.ver_publicacion, name='ver_publicacion'),
    path('like/<int:publicacion_id>/', views.toggle_like, name='toggle_like'),
    path('comentar/<int:publicacion_id>/', views.comentar, name='comentar'),
    path('comentario/eliminar/<int:comentario_id>/', views.eliminar_comentario, name='eliminar_comentario'),
]