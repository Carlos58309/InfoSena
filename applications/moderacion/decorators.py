# applications/moderacion/decorators.py
"""
Decoradores para aplicar moderación automática en views
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .moderacion_service import moderacion
import logging

logger = logging.getLogger(__name__)


def moderar_texto_post(campo_texto='contenido', redirect_url=None):
    """Decorador para moderar texto de un POST"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                texto = request.POST.get(campo_texto, '')
                if texto:
                    resultado = moderacion.moderar_texto(texto)
                    if not resultado['permitido']:
                        logger.warning(f"❌ Contenido bloqueado: {resultado['razon']}")
                        messages.error(request, f"⚠️ Tu contenido fue bloqueado: {resultado['razon']}")
                        return redirect(redirect_url or request.path)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def moderar_archivos_post(campo_archivos='archivos', max_archivos=10):
    """Decorador para moderar archivos de un POST"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                archivos = request.FILES.getlist(campo_archivos)
                if len(archivos) > max_archivos:
                    messages.error(request, f"❌ Máximo {max_archivos} archivos permitidos")
                    return redirect(request.path)
                for i, archivo in enumerate(archivos):
                    resultado = moderacion.moderar_archivo(archivo)
                    if not resultado['permitido']:
                        logger.warning(f"❌ Archivo {i+1} bloqueado: {resultado['razon']}")
                        messages.error(request, f"⚠️ Archivo '{archivo.name}' bloqueado: {resultado['razon']}")
                        return redirect(request.path)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def moderar_contenido_completo(
    campo_texto='contenido',
    campo_imagenes='imagenes',
    campo_videos='videos',
    max_imagenes=10,
    max_videos=5
):
    """Decorador completo que modera texto, imágenes y videos"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                errores = []

                texto = request.POST.get(campo_texto, '')
                if texto:
                    resultado_texto = moderacion.moderar_texto(texto)
                    if not resultado_texto['permitido']:
                        errores.append(f"Texto: {resultado_texto['razon']}")

                imagenes = request.FILES.getlist(campo_imagenes)
                if len(imagenes) > max_imagenes:
                    errores.append(f"Máximo {max_imagenes} imágenes permitidas")
                else:
                    for i, imagen in enumerate(imagenes):
                        resultado_img = moderacion.moderar_archivo(imagen)
                        if not resultado_img['permitido']:
                            errores.append(f"Imagen {i+1}: {resultado_img['razon']}")

                videos = request.FILES.getlist(campo_videos)
                if len(videos) > max_videos:
                    errores.append(f"Máximo {max_videos} videos permitidos")
                else:
                    for i, video in enumerate(videos):
                        resultado_vid = moderacion.moderar_archivo(video)
                        if not resultado_vid['permitido']:
                            errores.append(f"Video {i+1}: {resultado_vid['razon']}")

                if errores:
                    for error in errores:
                        messages.error(request, f"⚠️ {error}")
                    logger.warning(f"❌ Contenido bloqueado: {', '.join(errores)}")
                    return redirect(request.path)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def moderar_mensaje_chat(campo_mensaje='contenido'):
    """
    Decorador para mensajes de chat.

    Bloquea:
    - Palabras prohibidas (filtro local) → siempre
    - OpenAI categorías graves → siempre
    - Rate-limit/error → bloquea con mensaje amigable
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                mensaje = request.POST.get(campo_mensaje, '')
                if mensaje:
                    resultado = moderacion.moderar_texto(mensaje)

                    if not resultado['permitido']:
                        metodo = resultado.get('metodo', '')

                        # Palabras prohibidas → siempre bloquear
                        if metodo == 'filtro_local':
                            logger.warning(f"❌ Mensaje bloqueado (filtro local): {resultado['razon']}")
                            messages.error(request, "⚠️ Por favor, usa un lenguaje respetuoso")
                            return redirect(request.path)

                        # OpenAI detectó contenido grave
                        elif metodo == 'openai_api':
                            categorias_graves = [
                                'sexual', 'sexual/minors', 'violence/graphic',
                                'hate/threatening', 'self-harm/intent',
                                'harassment/threatening', 'illicit/violent'
                            ]
                            if any(cat in resultado.get('categorias_violadas', []) for cat in categorias_graves):
                                logger.warning(f"❌ Mensaje bloqueado (OpenAI grave): {resultado['razon']}")
                                messages.error(request, "⚠️ Tu mensaje contiene contenido inapropiado")
                                return redirect(request.path)

                        # Rate-limit o error → bloquear con mensaje amigable
                        elif metodo in ('error_rate_limit', 'error_fallback'):
                            messages.error(request, f"⚠️ {resultado['razon']}")
                            return redirect(request.path)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def validar_perfil(campo_nombre='nombre', campo_biografia='biografia'):
    """Decorador para validar datos de perfil"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                errores = []

                nombre = request.POST.get(campo_nombre, '')
                if nombre:
                    resultado_nombre = moderacion.validar_nombre_usuario(nombre)
                    if not resultado_nombre['permitido']:
                        errores.append(f"Nombre: {resultado_nombre['razon']}")

                biografia = request.POST.get(campo_biografia, '')
                if biografia:
                    resultado_bio = moderacion.validar_biografia(biografia)
                    if not resultado_bio['permitido']:
                        errores.append(f"Biografía: {resultado_bio['razon']}")

                if errores:
                    for error in errores:
                        messages.error(request, f"⚠️ {error}")
                    return redirect(request.path)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator