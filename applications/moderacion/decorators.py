# applications/moderacion/decorators.py
"""
Decoradores para moderación automática
Validan el contenido antes de guardar o procesar
"""

import logging
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from applications.moderacion.moderacion_service import ModeracionService

logger = logging.getLogger(__name__)


def moderar_mensaje_chat(view_func):
    """
    Decorador para moderar mensajes de chat antes de guardarlos
    Uso:
        @moderar_mensaje_chat
        def enviar_mensaje(request, chat_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Solo validar POST requests
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)
        
        try:
            # Obtener el contenido del mensaje
            import json
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                contenido = data.get('contenido', '')
            else:
                contenido = request.POST.get('contenido', '')
            
            if not contenido:
                return view_func(request, *args, **kwargs)
            
            # Moderar el contenido
            logger.info(f"🔍 Moderando mensaje de chat: {contenido[:50]}...")
            
            moderador = ModeracionService()
            resultado = moderador.moderar_texto(contenido)
            
            if resultado['bloqueado']:
                logger.warning(f"🚫 Mensaje bloqueado: {resultado['razon']}")
                
                # Si es JSON, retornar JSON
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu mensaje contiene contenido inapropiado y no puede ser enviado.',
                        'detalles': resultado['razon'],
                        'categorias': resultado['categorias_detectadas']
                    }, status=400)
                else:
                    # Si es form, lanzar ValidationError
                    raise ValidationError(
                        'Tu mensaje contiene contenido inapropiado y no puede ser enviado.'
                    )
            
            logger.info(f"✅ Mensaje aprobado")
            return view_func(request, *args, **kwargs)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Error en decorador de moderación: {e}")
            # En caso de error, permitir el mensaje (fail-open)
            return view_func(request, *args, **kwargs)
    
    return wrapper


def moderar_publicacion(view_func):
    """
    Decorador para moderar publicaciones antes de crearlas
    Uso:
        @moderar_publicacion
        def crear_publicacion(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)
        
        try:
            # Obtener datos de la publicación
            titulo = request.POST.get('titulo', '')
            contenido = request.POST.get('contenido', '')
            
            moderador = ModeracionService()
            
            # Moderar título
            if titulo:
                logger.info(f"🔍 Moderando título: {titulo[:50]}...")
                resultado_titulo = moderador.moderar_texto(titulo)
                
                if resultado_titulo['bloqueado']:
                    logger.warning(f"🚫 Título bloqueado: {resultado_titulo['razon']}")
                    raise ValidationError(
                        f'El título contiene contenido inapropiado: {resultado_titulo["razon"]}'
                    )
            
            # Moderar contenido
            if contenido:
                logger.info(f"🔍 Moderando contenido: {contenido[:50]}...")
                resultado_contenido = moderador.moderar_texto(contenido)
                
                if resultado_contenido['bloqueado']:
                    logger.warning(f"🚫 Contenido bloqueado: {resultado_contenido['razon']}")
                    raise ValidationError(
                        f'El contenido de la publicación es inapropiado: {resultado_contenido["razon"]}'
                    )
            
            logger.info("✅ Publicación aprobada")
            return view_func(request, *args, **kwargs)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Error en moderación de publicación: {e}")
            # En caso de error, permitir la publicación
            return view_func(request, *args, **kwargs)
    
    return wrapper


def moderar_comentario(view_func):
    """
    Decorador para moderar comentarios antes de crearlos
    Uso:
        @moderar_comentario
        def crear_comentario(request, publicacion_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)
        
        try:
            # Obtener contenido del comentario
            contenido = request.POST.get('contenido', '')
            
            if not contenido:
                return view_func(request, *args, **kwargs)
            
            # Moderar
            logger.info(f"🔍 Moderando comentario: {contenido[:50]}...")
            
            moderador = ModeracionService()
            resultado = moderador.moderar_texto(contenido)
            
            if resultado['bloqueado']:
                logger.warning(f"🚫 Comentario bloqueado: {resultado['razon']}")
                raise ValidationError(
                    f'Tu comentario contiene contenido inapropiado: {resultado["razon"]}'
                )
            
            logger.info("✅ Comentario aprobado")
            return view_func(request, *args, **kwargs)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Error en moderación de comentario: {e}")
            return view_func(request, *args, **kwargs)
    
    return wrapper