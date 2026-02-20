# applications/publicaciones/views.py - VERSIÓN CON MODERACIÓN IA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Publicacion, Like, Comentario, ArchivoPublicacion
from applications.registro.models import Bienestar
from applications.moderacion.moderacion_service import moderacion
from applications.moderacion.decorators import moderar_contenido_completo
import logging

logger = logging.getLogger(__name__)


@login_required
@moderar_contenido_completo(
    campo_texto='contenido',
    campo_imagenes='imagenes',
    campo_videos='videos',
    max_imagenes=10,
    max_videos=5
)
def crear_publicacion(request):
    """
    Vista para crear publicaciones - CON MODERACIÓN IA
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
        
        # ========================================
        # MODERACIÓN DE CONTENIDO - PASO 1: TÍTULO
        # ========================================
        logger.info(f"🔍 Moderando título de publicación")
        resultado_titulo = moderacion.moderar_texto(titulo)
        
        if not resultado_titulo['permitido']:
            logger.warning(f"❌ Título bloqueado: {resultado_titulo['razon']}")
            messages.error(
                request, 
                f"⚠️ Tu título fue bloqueado: {resultado_titulo['razon']}"
            )
            return render(request, 'crear_publicacion.html', {
                'usuario': datos_bienestar,
                'tipo_perfil': tipo_perfil,
                'categorias': Publicacion.CATEGORIA_CHOICES
            })
        
        # ========================================
        # MODERACIÓN DE CONTENIDO - PASO 2: TEXTO
        # ========================================
        # El decorador @moderar_contenido_completo ya validó el contenido
        # pero lo hacemos también aquí para registro completo
        
        try:
            # Obtener archivos
            imagenes = request.FILES.getlist('imagenes')
            videos = request.FILES.getlist('videos')
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📝 CREANDO PUBLICACIÓN CON MODERACIÓN")
            logger.info(f"   Autor: {datos_bienestar.nombre}")
            logger.info(f"   Título: {titulo}")
            logger.info(f"   Categoría: {categoria}")
            logger.info(f"   Imágenes: {len(imagenes)}")
            logger.info(f"   Videos: {len(videos)}")
            
            # ========================================
            # MODERACIÓN - PASO 3: ARCHIVOS MULTIMEDIA
            # ========================================
            # El decorador ya validó, pero registramos individualmente
            archivos_rechazados = []
            
            for i, imagen in enumerate(imagenes):
                resultado_img = moderacion.moderar_archivo(imagen)
                if not resultado_img['permitido']:
                    archivos_rechazados.append(f"Imagen {i+1}: {resultado_img['razon']}")
            
            for i, video in enumerate(videos):
                resultado_vid = moderacion.moderar_archivo(video)
                if not resultado_vid['permitido']:
                    archivos_rechazados.append(f"Video {i+1}: {resultado_vid['razon']}")
            
            if archivos_rechazados:
                for rechazo in archivos_rechazados:
                    messages.error(request, f"⚠️ {rechazo}")
                return render(request, 'crear_publicacion.html', {
                    'usuario': datos_bienestar,
                    'tipo_perfil': tipo_perfil,
                    'categorias': Publicacion.CATEGORIA_CHOICES
                })
            
            # ========================================
            # TODO APROBADO - CREAR PUBLICACIÓN
            # ========================================
            logger.info(f"✅ Contenido aprobado por IA - Creando publicación")
            
            # Crear la publicación (el signal también moderará)
            try:
                publicacion = Publicacion.objects.create(
                    autor=datos_bienestar,
                    titulo=titulo,
                    contenido=contenido,
                    categoria=categoria
                )
                
                logger.info(f"✅ Publicación creada con ID: {publicacion.id}")
                
            except ValidationError as e:
                # El signal rechazó la publicación
                logger.error(f"❌ Publicación rechazada por signal: {e}")
                messages.error(request, f"⚠️ {str(e)}")
                return render(request, 'crear_publicacion.html', {
                    'usuario': datos_bienestar,
                    'tipo_perfil': tipo_perfil,
                    'categorias': Publicacion.CATEGORIA_CHOICES
                })
            
            # Guardar archivos multimedia
            imagenes_guardadas = 0
            videos_guardados = 0
            errores = []
            
            for i, imagen in enumerate(imagenes):
                try:
                    archivo = ArchivoPublicacion.objects.create(
                        publicacion=publicacion,
                        tipo='imagen',
                        archivo=imagen,
                        orden=i
                    )
                    imagenes_guardadas += 1
                    logger.info(f"   ✅ Imagen {i+1} guardada: {archivo.archivo.name}")
                except Exception as e:
                    error_msg = f"Error guardando imagen {i+1}: {str(e)}"
                    logger.error(f"   ❌ {error_msg}")
                    errores.append(error_msg)
            
            for i, video in enumerate(videos):
                try:
                    archivo = ArchivoPublicacion.objects.create(
                        publicacion=publicacion,
                        tipo='video',
                        archivo=video,
                        orden=len(imagenes) + i
                    )
                    videos_guardados += 1
                    logger.info(f"   ✅ Video {i+1} guardado: {archivo.archivo.name}")
                except Exception as e:
                    error_msg = f"Error guardando video {i+1}: {str(e)}"
                    logger.error(f"   ❌ {error_msg}")
                    errores.append(error_msg)
            
            # Mensajes al usuario
            logger.info(f"{'='*80}\n")
            
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
            logger.error(f"\n❌ ERROR CRÍTICO AL CREAR PUBLICACIÓN:")
            logger.error(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            logger.info(f"{'='*80}\n")
            
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


# ========================================
# RESTO DE VISTAS (sin cambios mayores)
# ========================================

@login_required
def listar_publicaciones(request):
    """Vista para listar todas las publicaciones activas"""
    publicaciones = Publicacion.objects.filter(activa=True).prefetch_related('archivos')
    
    context = {
        'publicaciones': publicaciones,
    }
    return render(request, 'listar_publicaciones.html', context)


@login_required
def ver_publicacion(request, publicacion_id):
    """Vista para ver una publicación específica"""
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
    """Vista para ver las publicaciones del usuario de bienestar logueado"""
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')
    
    tipo_perfil = request.session['tipo_usuario']
    
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
    """Vista para eliminar una publicación"""
    if 'usuario_id' not in request.session:
        messages.error(request, "No autorizado")
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        
        if publicacion.autor != datos_bienestar:
            messages.error(request, "No tienes permiso para eliminar esta publicación")
            return redirect('perfil:perfiles')
        
        publicacion.delete()
        messages.success(request, "✅ Publicación eliminada exitosamente")
        
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
    except Exception as e:
        logger.error(f"Error al eliminar publicación: {e}")
        messages.error(request, "Error al eliminar la publicación")
    
    return redirect('perfil:perfiles')


@login_required
def toggle_like(request, publicacion_id):
    """Dar o quitar like a una publicación"""
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
    """Vista detallada de una publicación con comentarios"""
    publicacion = get_object_or_404(
        Publicacion.objects.prefetch_related('archivos', 'comentarios'),
        id=id
    )
    comentarios = publicacion.comentarios.all().order_by('fecha_creacion')
    
    if request.method == 'POST':
        if 'usuario_id' not in request.session:
            messages.error(request, "Debes iniciar sesión para comentar")
            return redirect('sesion:login')
        
        usuario_id = request.session['usuario_id']
        
        try:
            datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
            texto = request.POST.get('texto', '').strip()
            
            if texto:
                # MODERACIÓN DE COMENTARIO
                resultado = moderacion.moderar_texto(texto)
                
                if not resultado['permitido']:
                    messages.error(
                        request,
                        f"⚠️ Tu comentario fue bloqueado: {resultado['razon']}"
                    )
                else:
                    try:
                        Comentario.objects.create(
                            publicacion=publicacion,
                            autor=datos_bienestar,
                            contenido=texto
                        )
                        messages.success(request, "Comentario agregado")
                    except ValidationError as e:
                        messages.error(request, f"⚠️ {str(e)}")
                
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
    """Agregar un comentario a una publicación"""
    if request.method == 'POST':
        if 'usuario_id' not in request.session:
            messages.error(request, "Debes iniciar sesión para comentar")
            return redirect('sesion:login')
        
        usuario_id = request.session['usuario_id']
        
        try:
            datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
            publicacion = get_object_or_404(Publicacion, id=publicacion_id)
            contenido = request.POST.get('contenido', '').strip()
            
            if contenido:
                # MODERACIÓN DE COMENTARIO
                resultado = moderacion.moderar_texto(contenido)
                
                if not resultado['permitido']:
                    messages.error(
                        request,
                        f"⚠️ Tu comentario fue bloqueado: {resultado['razon']}"
                    )
                else:
                    try:
                        Comentario.objects.create(
                            publicacion=publicacion,
                            autor=datos_bienestar,
                            contenido=contenido
                        )
                        messages.success(request, "Comentario agregado")
                    except ValidationError as e:
                        messages.error(request, f"⚠️ {str(e)}")
            else:
                messages.error(request, "El comentario no puede estar vacío")
        
        except Bienestar.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
    
    return redirect(request.META.get('HTTP_REFERER', 'perfil:perfiles'))


@login_required
def eliminar_comentario(request, comentario_id):
    """Eliminar un comentario"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacion = comentario.publicacion
    
    if 'usuario_id' not in request.session:
        messages.error(request, "No autorizado")
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    
    try:
        datos_bienestar = Bienestar.objects.get(numero_documento=usuario_id)
        
        if datos_bienestar == comentario.autor or datos_bienestar == publicacion.autor:
            comentario.delete()
            messages.success(request, "Comentario eliminado")
        else:
            messages.error(request, "No tienes permiso para eliminar este comentario")
    
    except Bienestar.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
    
    return redirect(request.META.get('HTTP_REFERER', 'perfil:perfiles'))