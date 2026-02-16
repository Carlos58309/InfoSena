# publicaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Publicacion, Like, Comentario, ArchivoPublicacion
from applications.registro.models import Bienestar

@login_required
def crear_publicacion(request):
    """
    Vista para crear publicaciones - VERSIÓN FINAL CORREGIDA
    """
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
        # IMPORTANTE: Obtener el objeto Bienestar directamente
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        
        # DEBUG: Verificar el tipo de objeto
        print(f"\n🔍 VERIFICACIÓN DE OBJETO:")
        print(f"   Tipo de objeto: {type(datos_bienestar)}")
        print(f"   Es Bienestar: {isinstance(datos_bienestar, Bienestar)}")
        print(f"   Nombre: {datos_bienestar.nombre}")
        print(f"   Documento: {datos_bienestar.numero_documento}")
        
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario de bienestar no encontrado")
        return redirect('perfil:perfiles')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        titulo = request.POST.get('titulo', '').strip()
        contenido = request.POST.get('contenido', '').strip()
        categoria = request.POST.get('categoria', 'informacion')
        
        # Validación básica
        if not titulo or not contenido:
            messages.error(request, "El título y contenido son obligatorios")
            return render(request, 'crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
        
        if len(contenido) < 20:
            messages.error(request, "El contenido debe tener al menos 20 caracteres")
            return render(request, 'crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
        
        try:
            # Obtener archivos
            imagenes = request.FILES.getlist('imagenes')
            videos = request.FILES.getlist('videos')
            
            print("\n" + "="*80)
            print("📝 CREANDO PUBLICACIÓN")
            print(f"   Autor: {datos_bienestar.nombre}")
            print(f"   Tipo autor: {type(datos_bienestar)}")
            print(f"   Título: {titulo}")
            print(f"   Categoría: {categoria}")
            print(f"   Imágenes: {len(imagenes)}")
            print(f"   Videos: {len(videos)}")
            
            # Validar cantidad de archivos
            if len(imagenes) > 10:
                messages.error(request, "Máximo 10 imágenes permitidas")
                return render(request, 'crear_publicacion.html', {
                    'usuario': datos_bienestar,
                    'tipo_perfil': tipo_perfil,
                    'categorias': Publicacion.CATEGORIA_CHOICES
                })
            
            if len(videos) > 5:
                messages.error(request, "Máximo 5 videos permitidos")
                return render(request, 'crear_publicacion.html', {
                    'usuario': datos_bienestar,
                    'tipo_perfil': tipo_perfil,
                    'categorias': Publicacion.CATEGORIA_CHOICES
                })
            
            # Validar tamaño de archivos
            MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
            MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
            
            for imagen in imagenes:
                if imagen.size > MAX_IMAGE_SIZE:
                    messages.error(request, f"La imagen '{imagen.name}' excede el tamaño máximo de 10MB")
                    return render(request, 'crear_publicacion.html', {
                        'usuario': datos_bienestar,
                        'tipo_perfil': tipo_perfil,
                        'categorias': Publicacion.CATEGORIA_CHOICES
                    })
            
            for video in videos:
                if video.size > MAX_VIDEO_SIZE:
                    messages.error(request, f"El video '{video.name}' excede el tamaño máximo de 50MB")
                    return render(request, 'crear_publicacion.html', {
                        'usuario': datos_bienestar,
                        'tipo_perfil': tipo_perfil,
                        'categorias': Publicacion.CATEGORIA_CHOICES
                    })
            
            # CRÍTICO: Asegurarse de usar el objeto Bienestar directamente
            print(f"\n🔧 CREANDO PUBLICACIÓN CON:")
            print(f"   autor={datos_bienestar} (tipo: {type(datos_bienestar).__name__})")
            
            # Crear la publicación
            publicacion = Publicacion.objects.create(
                autor=datos_bienestar,  # Objeto Bienestar directo
                titulo=titulo,
                contenido=contenido,
                categoria=categoria
            )
            
            print(f"✅ Publicación creada con ID: {publicacion.id}")
            
            # Contador de archivos guardados
            imagenes_guardadas = 0
            videos_guardados = 0
            errores = []
            
            # Guardar imágenes
            for i, imagen in enumerate(imagenes):
                try:
                    archivo = ArchivoPublicacion.objects.create(
                        publicacion=publicacion,
                        tipo='imagen',
                        archivo=imagen,
                        orden=i
                    )
                    imagenes_guardadas += 1
                    print(f"   ✅ Imagen {i+1} guardada: {archivo.archivo.name}")
                except Exception as e:
                    error_msg = f"Error guardando imagen {i+1}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    errores.append(error_msg)
            
            # Guardar videos
            for i, video in enumerate(videos):
                try:
                    archivo = ArchivoPublicacion.objects.create(
                        publicacion=publicacion,
                        tipo='video',
                        archivo=video,
                        orden=len(imagenes) + i
                    )
                    videos_guardados += 1
                    print(f"   ✅ Video {i+1} guardado: {archivo.archivo.name}")
                except Exception as e:
                    error_msg = f"Error guardando video {i+1}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    errores.append(error_msg)
            
            # Verificación final
            total_archivos = ArchivoPublicacion.objects.filter(publicacion=publicacion).count()
            print(f"\n📊 RESUMEN:")
            print(f"   Total archivos guardados en DB: {total_archivos}")
            print(f"   Imágenes: {imagenes_guardadas}")
            print(f"   Videos: {videos_guardados}")
            print("="*80 + "\n")
            
            # Mensajes al usuario
            if imagenes_guardadas > 0 or videos_guardados > 0:
                messages.success(
                    request, 
                    f"✅ Publicación creada exitosamente con {imagenes_guardadas} imagen(es) y {videos_guardados} video(s)"
                )
            else:
                messages.warning(
                    request, 
                    "⚠️ Publicación creada pero no se guardaron archivos multimedia"
                )
            
            if errores:
                for error in errores:
                    messages.warning(request, error)
            
            return redirect('perfil:perfiles')
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO AL CREAR PUBLICACIÓN:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            
            messages.error(request, f"Error al crear la publicación: {str(e)}")
            return render(request, 'crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
    
    # GET request
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
    publicaciones = Publicacion.objects.filter(activa=True).prefetch_related('archivos')
    
    context = {
        'publicaciones': publicaciones,
    }
    return render(request, 'listar_publicaciones.html', context)


@login_required
def ver_publicacion(request, publicacion_id):
    """
    Vista para ver una publicación específica
    """
    publicacion = get_object_or_404(
        Publicacion.objects.prefetch_related('archivos', 'comentarios'),
        id=publicacion_id,
        activa=True
    )
    
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
        publicaciones = Publicacion.objects.filter(
            autor=datos_bienestar
        ).prefetch_related('archivos')
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
        return redirect('perfil:perfiles')
    
    context = {
        'publicaciones': publicaciones,
        'usuario': datos_bienestar,
    }
    return render(request, 'mis_publicaciones.html', context)


@login_required
def eliminar_publicacion(request, publicacion_id):
    """
    Vista para eliminar una publicación - Solo el autor puede eliminar
    """
    # Verificar sesión
    if 'usuario_id' not in request.session:
        messages.error(request, "No autorizado")
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        
        # Verificar que el usuario sea el autor
        if publicacion.autor != datos_bienestar:
            messages.error(request, "No tienes permiso para eliminar esta publicación")
            return redirect('perfil:perfiles')
        
        # Eliminar la publicación (esto también eliminará los archivos relacionados por CASCADE)
        publicacion.delete()
        messages.success(request, "✅ Publicación eliminada exitosamente")
        
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
    except Exception as e:
        print(f"Error al eliminar publicación: {e}")
        messages.error(request, "Error al eliminar la publicación")
    
    return redirect('perfil:perfiles')


@login_required
def toggle_like(request, publicacion_id):
    """
    Dar o quitar like a una publicación
    """
    # Verificar sesión
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        
        like, created = Like.objects.get_or_create(
            usuario=datos_bienestar,
            publicacion=publicacion
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'likes_count': publicacion.total_likes()
        })
    
    except Bienestar.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)


@login_required
def detalle_publicacion(request, id):
    """
    Vista detallada de una publicación con comentarios
    """
    publicacion = get_object_or_404(
        Publicacion.objects.prefetch_related('archivos', 'comentarios'),
        id=id
    )
    comentarios = publicacion.comentarios.all().order_by('fecha_creacion')
    
    # Verificar sesión para comentarios
    if request.method == 'POST':
        if 'usuario_id' not in request.session:
            messages.error(request, "Debes iniciar sesión para comentar")
            return redirect('sesion:login')
        
        usuario_id = request.session['usuario_id']
        
        try:
            datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
            texto = request.POST.get('texto')
            
            if texto:
                Comentario.objects.create(
                    publicacion=publicacion,
                    autor=datos_bienestar,
                    contenido=texto
                )
                messages.success(request, "Comentario agregado")
                return redirect('publicaciones:detalle', id=id)
        
        except Bienestar.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
    
    context = {
        'publicacion': publicacion,
        'comentarios': comentarios
    }
    return render(request, 'detalle_publicacion.html', context)


@login_required
def comentar(request, publicacion_id):
    """
    Agregar un comentario a una publicación
    """
    if request.method == 'POST':
        # Verificar sesión
        if 'usuario_id' not in request.session:
            messages.error(request, "Debes iniciar sesión para comentar")
            return redirect('sesion:login')
        
        usuario_id = request.session['usuario_id']
        
        try:
            datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
            publicacion = get_object_or_404(Publicacion, id=publicacion_id)
            contenido = request.POST.get('contenido')
            
            if contenido:
                Comentario.objects.create(
                    publicacion=publicacion,
                    autor=datos_bienestar,
                    contenido=contenido
                )
                messages.success(request, "Comentario agregado")
            else:
                messages.error(request, "El comentario no puede estar vacío")
        
        except Bienestar.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
    
    return redirect(request.META.get('HTTP_REFERER', 'perfil:perfiles'))


@login_required
def eliminar_comentario(request, comentario_id):
    """
    Eliminar un comentario (solo el autor o el autor de la publicación)
    """
    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacion = comentario.publicacion
    
    # Verificar sesión
    if 'usuario_id' not in request.session:
        messages.error(request, "No autorizado")
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        
        # Verificar permisos: autor del comentario o autor de la publicación
        if datos_bienestar == comentario.autor or datos_bienestar == publicacion.autor:
            comentario.delete()
            messages.success(request, "Comentario eliminado")
        else:
            messages.error(request, "No tienes permiso para eliminar este comentario")
    
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
    
    return redirect(request.META.get('HTTP_REFERER', 'perfil:perfiles'))