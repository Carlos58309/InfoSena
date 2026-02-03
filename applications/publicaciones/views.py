from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Publicacion, Like, Comentario
from applications.registro.models import Bienestar

@login_required
def crear_publicacion(request):
    """
    Vista para crear publicaciones - Solo para usuarios de bienestar
    """
    if request.session.get('tipo_usuario') != 'bienestar':
        messages.error(request, "No tienes permiso para crear publicaciones")
        return redirect('perfil:perfiles')
    # Verificar sesión
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')
    
    tipo_perfil = request.session['tipo_usuario']
    
    # Verificar que sea usuario de bienestar
    if tipo_perfil != 'bienestar':
        messages.error(request, "No tienes permisos para crear publicaciones")
        return redirect('perfil:perfiles')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
        return redirect('perfil:perfiles')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        categoria = request.POST.get('categoria')
        imagen = request.FILES.get('imagen')
        
        # Validación básica
        if not titulo or not contenido:
            messages.error(request, "El título y contenido son obligatorios")
            return render(request, 'publicaciones/crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
        
        if len(contenido) < 20:
            messages.error(request, "El contenido debe tener al menos 20 caracteres")
            return render(request, 'publicaciones/crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
        
        try:
            # Crear la publicación - CAMBIO AQUÍ
            publicacion = Publicacion(
                autor=datos_bienestar,  # Pasar el objeto directamente
                titulo=titulo,
                contenido=contenido,
                categoria=categoria
            )
            
            # Asignar la imagen si existe
            if imagen:
                publicacion.imagen = imagen
            
            # Guardar
            publicacion.save()
            
            messages.success(request, "✅ Publicación creada exitosamente")
            return redirect('perfil:perfiles')
            
        except Exception as e:
            print(f"Error al crear publicación: {e}")  # Para debugging
            messages.error(request, f"Error al crear la publicación: {str(e)}")
    
    context = {
        'usuario': datos_bienestar,
        'tipo_perfil': tipo_perfil,
        'categorias': Publicacion.CATEGORIA_CHOICES
    }
    return render(request, 'crear_publicacion.html', context)


@login_required
def listar_publicaciones(request):
    """
    Vista para listar todas las publicaciones activas
    """
    publicaciones = Publicacion.objects.filter(activa=True)
    
    context = {
        'publicaciones': publicaciones,
    }
    return render(request, 'listar_publicaciones.html', context)


@login_required
def ver_publicacion(request, publicacion_id):
    """
    Vista para ver una publicación específica
    """
    publicacion = get_object_or_404(Publicacion, id=publicacion_id, activa=True)
    
    context = {
        'publicacion': publicacion,
    }
    return render(request, 'ver_publicacion.html', context)


@login_required
def mis_publicaciones(request):
    """
    Vista para ver las publicaciones del usuario de bienestar logueado
    """
    # Verificar sesión
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')
    
    tipo_perfil = request.session['tipo_usuario']
    
    # Verificar que sea usuario de bienestar
    if tipo_perfil != 'bienestar':
        messages.error(request, "No tienes permisos para ver esta sección")
        return redirect('perfil:perfiles')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        publicaciones = Publicacion.objects.filter(autor=datos_bienestar)
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
        return redirect('perfil:perfiles')
    
    context = {
        'publicaciones': publicaciones,
        'usuario': datos_bienestar,
    }
    return render(request, 'mis_publicaciones.html', context)

@login_required
def toggle_like(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)

    like, created = Like.objects.get_or_create(
        usuario=request.user,
        publicacion=publicacion
    )

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'likes_count': publicacion.likes.count()
    })

@login_required
def detalle_publicacion(request, id):
    publicacion = get_object_or_404(Publicacion, id=id)
    comentarios = publicacion.comentarios.all().order_by('fecha')

    if request.method == 'POST':
        texto = request.POST.get('texto')
        if texto:
            Comentario.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                texto=texto
            )
            return redirect('publicaciones:detalle', id=id)

    return render(request, 'detalle_publicacion.html', {
        'publicacion': publicacion,
        'comentarios': comentarios
    })

@login_required
def comentar(request, publicacion_id):
    if request.method == 'POST':
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)

        Comentario.objects.create(
            publicacion=publicacion,
            autor=request.user,
            contenido=request.POST.get('contenido')
        )

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacion = comentario.publicacion

    if (
        request.user == comentario.autor or
        request.user == publicacion.autor.user
    ):
        comentario.delete()
    else:
        messages.error(request, "No tienes permiso para eliminar este comentario")

    return redirect(request.META.get('HTTP_REFERER'))