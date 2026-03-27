# applications/moderacion/signals.py
"""
Signals para moderación automática
Se ejecutan ANTES de guardar los modelos en la base de datos
"""

import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from applications.moderacion.moderacion_service import ModeracionService

logger = logging.getLogger(__name__)

# Instancia única del servicio de moderación
_moderador = None

def get_moderador():
    """Obtener instancia del moderador (singleton)"""
    global _moderador
    if _moderador is None:
        _moderador = ModeracionService()
    return _moderador


# ============================================================
# SIGNALS PARA MENSAJES DE CHAT
# ============================================================

@receiver(pre_save, sender='chat.Mensaje')
def moderar_mensaje_antes_de_guardar(sender, instance, **kwargs):
    if instance.pk is not None:
        return

    contenido = instance.contenido

    if not contenido or not contenido.strip():
        return

    try:
        # ← NUEVO: desencriptar antes de moderar
        from applications.chat.encryption import desencriptar
        contenido_plano = desencriptar(contenido)
    except Exception:
        contenido_plano = contenido  # si falla, usar tal cual

    try:
        logger.info(f"🔍 [SIGNAL] Moderando mensaje: {contenido_plano[:50]}...")

        moderador = get_moderador()
        resultado = moderador.moderar_texto(contenido_plano)  # ← texto plano

        if resultado['bloqueado']:
            logger.warning(f"🚫 [SIGNAL] Mensaje bloqueado: {resultado['razon']}")
            raise ValidationError(
                f"Tu mensaje contiene contenido inapropiado y no puede ser enviado. "
                f"Razón: {resultado['razon']}"
            )

        logger.info(f"✅ [SIGNAL] Mensaje aprobado")

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"❌ [SIGNAL] Error al moderar mensaje: {e}")
        pass


# ============================================================
# SIGNALS PARA PUBLICACIONES
# ============================================================

@receiver(pre_save, sender='publicaciones.Publicacion')
def moderar_publicacion_antes_de_guardar(sender, instance, **kwargs):
    """
    Modera publicaciones antes de guardarlas en la BD
    Valida tanto el título como el contenido
    """
    # Solo moderar publicaciones nuevas
    if instance.pk is not None:
        return
    
    moderador = get_moderador()
    
    # Moderar título
    if instance.titulo:
        try:
            logger.info(f"🔍 [SIGNAL] Moderando título: {instance.titulo[:50]}...")
            
            resultado_titulo = moderador.moderar_texto(instance.titulo)
            
            if resultado_titulo['bloqueado']:
                logger.warning(f"🚫 [SIGNAL] Título bloqueado: {resultado_titulo['razon']}")
                raise ValidationError(
                    f"El título contiene contenido inapropiado. "
                    f"Razón: {resultado_titulo['razon']}"
                )
            
            logger.info(f"✅ [SIGNAL] Título aprobado")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ [SIGNAL] Error al moderar título: {e}")
    
    # Moderar contenido
    if instance.contenido:
        try:
            logger.info(f"🔍 [SIGNAL] Moderando contenido: {instance.contenido[:50]}...")
            
            resultado_contenido = moderador.moderar_texto(instance.contenido)
            
            if resultado_contenido['bloqueado']:
                logger.warning(f"🚫 [SIGNAL] Contenido bloqueado: {resultado_contenido['razon']}")
                raise ValidationError(
                    f"El contenido de la publicación es inapropiado. "
                    f"Razón: {resultado_contenido['razon']}"
                )
            
            logger.info(f"✅ [SIGNAL] Contenido aprobado")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ [SIGNAL] Error al moderar contenido: {e}")


# ============================================================
# SIGNALS PARA COMENTARIOS
# ============================================================

@receiver(pre_save, sender='publicaciones.Comentario')
def moderar_comentario_antes_de_guardar(sender, instance, **kwargs):
    """
    Modera comentarios antes de guardarlos en la BD
    """
    # Solo moderar comentarios nuevos
    if instance.pk is not None:
        return
    
    contenido = instance.contenido
    
    if not contenido or not contenido.strip():
        return
    
    try:
        logger.info(f"🔍 [SIGNAL] Moderando comentario: {contenido[:50]}...")
        
        moderador = get_moderador()
        resultado = moderador.moderar_texto(contenido)
        
        if resultado['bloqueado']:
            logger.warning(f"🚫 [SIGNAL] Comentario bloqueado: {resultado['razon']}")
            raise ValidationError(
                f"Tu comentario contiene contenido inapropiado. "
                f"Razón: {resultado['razon']}"
            )
        
        logger.info(f"✅ [SIGNAL] Comentario aprobado")
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"❌ [SIGNAL] Error al moderar comentario: {e}")
        pass


# ============================================================
# LOGGING DE INICIALIZACIÓN
# ============================================================

logger.info("✅ Signals de moderación registrados correctamente")
logger.info("   → Mensaje (chat.Mensaje)")
logger.info("   → Publicación (publicaciones.Publicacion)")
logger.info("   → Comentario (publicaciones.Comentario)")