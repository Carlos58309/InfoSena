# urls.py de la app publicaciones

from django.urls import path
from . import views

app_name = 'publicaciones'

urlpatterns = [
    # Crear y listar publicaciones
    path('crear/', views.crear_publicacion, name='crear_publicacion'),
    path('listar/', views.listar_publicaciones, name='listar_publicaciones'),
    path('mis-publicaciones/', views.mis_publicaciones, name='mis_publicaciones'),
    
    # Ver y gestionar publicaciones
    path('<int:publicacion_id>/', views.ver_publicacion, name='ver_publicacion'),
    path('detalle/<int:id>/', views.detalle_publicacion, name='detalle'),
    path('eliminar/<int:publicacion_id>/', views.eliminar_publicacion, name='eliminar_publicacion'),
    
    # Likes
    path('like/<int:publicacion_id>/', views.toggle_like, name='toggle_like'),
    
    # Comentarios
    path('comentar/<int:publicacion_id>/', views.comentar, name='comentar'),
    path('comentario/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
]