"""
URL configuration for info project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.index.urls')),                      # Página principal
    path('sesion/', include(('applications.sesion.urls', 'sesion'))),  # login, dashboard, etc.
    path('busqueda/', include('applications.busqueda.urls')),
    path('registro/', include(('applications.registro.urls', 'registro'), namespace='registro')),   
    path('perfil/', include('applications.perfil.urls')),  # tu app perfil 
    path('chat/', include('applications.chat.urls')),
    path('amistades/', include('applications.amistades.urls')),
    path('publicaciones/', include('applications.publicaciones.urls')),#publicaciones
    path('notificaciones/', include('applications.notificaciones.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)