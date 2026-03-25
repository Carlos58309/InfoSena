# applications/publicaciones/views.py - edicion
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Publicacion, Like, Comentario, ArchivoPublicacion
from applications.registro.models import Bienestar, Aprendiz, Instructor
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from applications.sesion.decorators import sesion_requerida

def get_usuario_actual(session):
    usuario_id = session.get('usuario_id')
    tipo = session.get('tipo_usuario')

    if not usuario_id or not tipo:
        return None, None

    try:
        if tipo == 'aprendiz':
            usuario = Aprendiz.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Aprendiz)
        elif tipo == 'instructor':
            usuario = Instructor.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Instructor)
        elif tipo == 'bienestar':
            usuario = Bienestar.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Bienestar)
        else:
            return None, None
        return usuario, ct
    except Exception as e:
        print(f"❌ get_usuario_actual error: {e}")
        return None, None

@sesion_requerida
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



def listar_publicaciones(request):
    """
    Vista para listar todas las publicaciones activas
    """
    publicaciones = Publicacion.objects.filter(activa=True).prefetch_related('archivos')
    
    context = {
        'publicaciones': publicaciones,
    }
    return render(request, 'listar_publicaciones.html', context)



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


@sesion_requerida
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


@sesion_requerida
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

def get_usuario_actual(session):
    """
    Devuelve (objeto_usuario, content_type) sea Aprendiz, Instructor o Bienestar
    """
    usuario_id = session.get('usuario_id')
    tipo = session.get('tipo_usuario')

    if not usuario_id or not tipo:
        return None, None

    try:
        if tipo == 'aprendiz':
            usuario = Aprendiz.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Aprendiz)
        elif tipo == 'instructor':
            usuario = Instructor.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Instructor)
        elif tipo == 'bienestar':
            usuario = Bienestar.objects.get(numero_documento=usuario_id)
            ct = ContentType.objects.get_for_model(Bienestar)
        else:
            return None, None
        return usuario, ct
    except Exception:
        return None, None

def usuario_dio_like(publicacion, usuario, ct):
    """Verifica si un usuario específico dio like a una publicación"""
    if not usuario or not ct:
        return False
    return Like.objects.filter(
        publicacion=publicacion,
        content_type=ct,
        object_id=str(usuario.numero_documento)
    ).exists()

@sesion_requerida
def toggle_like(request, publicacion_id):
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    usuario, ct = get_usuario_actual(request.session)
    if not usuario:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

    try:
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)

        like_existente = Like.objects.filter(
            publicacion=publicacion,
            content_type=ct,
            object_id=usuario.numero_documento
        ).first()

        if like_existente:
            like_existente.delete()
            liked = False
        else:
            Like.objects.create(
                publicacion=publicacion,
                content_type=ct,
                object_id=usuario.numero_documento
            )
            liked = True

        return JsonResponse({
            'liked': liked,
            'likes_count': publicacion.likes.count()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


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


@sesion_requerida
def comentar(request, publicacion_id):
    if request.method == 'POST':
        if 'usuario_id' not in request.session:
            return JsonResponse({'error': 'No autenticado'}, status=401)

        usuario, ct = get_usuario_actual(request.session)
        
        print(f"🔍 usuario: {usuario}")
        print(f"🔍 ct: {ct}")
        
        if not usuario:
            print(f"❌ usuario es None — tipo: {request.session.get('tipo_usuario')}, id: {request.session.get('usuario_id')}")
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

        try:
            publicacion = get_object_or_404(Publicacion, id=publicacion_id)
            contenido = request.POST.get('contenido', '').strip()
            
            print(f"🔍 contenido: '{contenido}'")
            print(f"🔍 object_id a guardar: {usuario.numero_documento}")

            if not contenido:
                return JsonResponse({'error': 'Comentario vacío'}, status=400)

            comentario = Comentario.objects.create(
                publicacion=publicacion,
                content_type=ct,
                object_id=usuario.numero_documento,
                contenido=contenido
            )
            print(f"✅ Comentario creado ID: {comentario.id}")

            return JsonResponse({
                'ok': True,
                'autor': usuario.nombre,
                'contenido': comentario.contenido,
                'fecha': 'Justo ahora',
                'foto': usuario.foto.url if usuario.foto else None,
                'total': publicacion.comentarios.count()
            })

        except Exception as e:
            import traceback
            print("❌ ERROR COMPLETO EN COMENTAR:")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@sesion_requerida
@require_POST
def eliminar_comentario(request, comentario_id):
    """Elimina un comentario SOLO si el usuario logueado es el autor."""
    
    # Verificar sesión
    if 'usuario_id' not in request.session:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=401)

    usuario, ct = get_usuario_actual(request.session)
    if not usuario:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    try:
        comentario = Comentario.objects.get(id=comentario_id)
    except Comentario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Comentario no encontrado'}, status=404)

    # ✅ Verificar que el que pide eliminar es el autor
    if str(comentario.object_id) != str(usuario.numero_documento):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para eliminar este comentario'}, status=403)

    publicacion_id = comentario.publicacion.id
    comentario.delete()
    
    total = Comentario.objects.filter(publicacion_id=publicacion_id).count()
    return JsonResponse({'ok': True, 'total': total})