from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Publicacion, Like, Comentario, ArchivoPublicacion
from applications.registro.models import Bienestar

@login_required
def crear_publicacion(request):
    """
    Vista para crear publicaciones - VERSIÓN CON DEBUGGING CORREGIDO
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
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
        return redirect('perfil:perfiles')
    
    if request.method == 'POST':
        # ================================================================
        # DEBUGGING SIN ACCEDER A request.body
        # ================================================================
        print("\n" + "="*100)
        print("🔍 DEBUGGING - CREAR PUBLICACIÓN")
        print("="*100)
        
        # Headers importantes (SIN leer request.body)
        print(f"\n📨 HEADERS:")
        print(f"   Content-Type: {request.META.get('CONTENT_TYPE', 'No encontrado')}")
        print(f"   Content-Length: {request.META.get('CONTENT_LENGTH', 'No encontrado')}")
        
        # Datos POST
        print(f"\n📝 DATOS POST:")
        print(f"   POST.keys(): {list(request.POST.keys())}")
        
        # Archivos - Verificación
        print(f"\n📁 ARCHIVOS:")
        print(f"   request.FILES.keys(): {list(request.FILES.keys())}")
        print(f"   request.FILES vacío: {len(request.FILES) == 0}")
        
        imagenes = request.FILES.getlist('imagenes')
        videos = request.FILES.getlist('videos')
        
        print(f"\n📷 IMÁGENES:")
        print(f"   Cantidad: {len(imagenes)}")
        for idx, img in enumerate(imagenes, 1):
            print(f"   Imagen {idx}: {img.name} ({img.size} bytes)")
        
        print(f"\n🎥 VIDEOS:")
        print(f"   Cantidad: {len(videos)}")
        for idx, vid in enumerate(videos, 1):
            print(f"   Video {idx}: {vid.name} ({vid.size} bytes)")
        
        print("="*100 + "\n")
        
        # Obtener datos del formulario
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        categoria = request.POST.get('categoria')
        
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
            # Crear la publicación
            publicacion = Publicacion.objects.create(
                autor=datos_bienestar,
                titulo=titulo,
                contenido=contenido,
                categoria=categoria
            )
            
            print(f"✅ Publicación creada: ID {publicacion.id}")
            
            # Contador de archivos guardados
            imagenes_guardadas = 0
            videos_guardados = 0
            
            # Guardar imágenes
            if len(imagenes) > 0:
                print(f"\n💾 GUARDANDO {len(imagenes)} IMÁGENES:")
                for i, imagen in enumerate(imagenes):
                    try:
                        archivo = ArchivoPublicacion.objects.create(
                            publicacion=publicacion,
                            tipo='imagen',
                            archivo=imagen,
                            orden=i
                        )
                        imagenes_guardadas += 1
                        print(f"   ✅ Imagen {i+1} guardada - ID: {archivo.id} - Ruta: {archivo.archivo.name}")
                    except Exception as e:
                        print(f"   ❌ Error guardando imagen {i+1}: {e}")
            else:
                print(f"\n⚠️ NO HAY IMÁGENES PARA GUARDAR")
            
            # Guardar videos
            if len(videos) > 0:
                print(f"\n💾 GUARDANDO {len(videos)} VIDEOS:")
                for i, video in enumerate(videos):
                    try:
                        archivo = ArchivoPublicacion.objects.create(
                            publicacion=publicacion,
                            tipo='video',
                            archivo=video,
                            orden=len(imagenes) + i
                        )
                        videos_guardados += 1
                        print(f"   ✅ Video {i+1} guardado - ID: {archivo.id} - Ruta: {archivo.archivo.name}")
                    except Exception as e:
                        print(f"   ❌ Error guardando video {i+1}: {e}")
            else:
                print(f"\n⚠️ NO HAY VIDEOS PARA GUARDAR")
            
            # Verificación final
            archivos_db = ArchivoPublicacion.objects.filter(publicacion=publicacion)
            print(f"\n📊 RESUMEN:")
            print(f"   Total archivos en DB: {archivos_db.count()}")
            for archivo in archivos_db:
                print(f"      - {archivo.tipo}: {archivo.archivo.name}")
            
            print("="*100 + "\n")
            
            if imagenes_guardadas > 0 or videos_guardados > 0:
                messages.success(request, f"✅ Publicación creada con {imagenes_guardadas} imágenes y {videos_guardados} videos")
            else:
                messages.warning(request, "⚠️ Publicación creada pero sin archivos multimedia")
            
            return redirect('perfil:perfiles')
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*100 + "\n")
            
            messages.error(request, "Hubo un error al crear la publicación. Por favor, intenta de nuevo.")
            return render(request, 'crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
    
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