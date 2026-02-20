# applications/moderacion/signals.py
"""
Signals para moderar contenido automáticamente antes de guardar
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .moderacion_service import moderacion
from .models import RegistroModeracion
import logging

logger = logging.getLogger(__name__)


def registrar_moderacion(usuario, tipo_contenido, resultado_moderacion,
                         contenido_texto=None, archivo_url=None, request=None):
    """Helper para registrar una moderación en la base de datos"""
    try:
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        RegistroModeracion.objects.create(
            usuario=usuario,
            tipo_contenido=tipo_contenido,
            resultado='aprobado' if resultado_moderacion['permitido'] else 'bloqueado',
            contenido_texto=contenido_texto[:500] if contenido_texto else None,
            archivo_url=archivo_url,
            razon=resultado_moderacion.get('razon', ''),
            categorias_violadas=resultado_moderacion.get('categorias_violadas', []),
            score_confianza=resultado_moderacion.get('score_confianza', {}),
            metodo_usado=resultado_moderacion.get('metodo', 'openai_api'),
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error registrando moderación: {e}")


# ─────────────────────────────────────────────────────────────
# PUBLICACIONES
# ─────────────────────────────────────────────────────────────

@receiver(pre_save, sender='publicaciones.Publicacion')
def moderar_publicacion(sender, instance, **kwargs):
    """Modera contenido de publicaciones antes de guardar"""
    if instance.pk is None:
        logger.info(f"🔍 Moderando publicación: {instance.titulo}")

        resultado_titulo = moderacion.moderar_texto(instance.titulo)
        if not resultado_titulo['permitido']:
            logger.warning(f"❌ Título bloqueado: {resultado_titulo['razon']}")
            raise ValidationError({'titulo': f"Título bloqueado: {resultado_titulo['razon']}"})

        resultado_contenido = moderacion.moderar_texto(instance.contenido)
        if not resultado_contenido['permitido']:
            logger.warning(f"❌ Contenido bloqueado: {resultado_contenido['razon']}")
            try:
                from applications.usuarios.models import Usuario
                usuario = Usuario.objects.filter(documento=instance.autor.numero_documento).first()
                registrar_moderacion(
                    usuario=usuario,
                    tipo_contenido='texto',
                    resultado_moderacion=resultado_contenido,
                    contenido_texto=instance.contenido
                )
            except Exception:
                pass
            raise ValidationError({'contenido': f"Contenido bloqueado: {resultado_contenido['razon']}"})

        logger.info(f"✅ Publicación aprobada: {instance.titulo}")


# ─────────────────────────────────────────────────────────────
# COMENTARIOS
# ─────────────────────────────────────────────────────────────

@receiver(pre_save, sender='publicaciones.Comentario')
def moderar_comentario(sender, instance, **kwargs):
    """Modera comentarios antes de guardar"""
    if instance.pk is None:
        logger.info("🔍 Moderando comentario")

        resultado = moderacion.moderar_texto(instance.contenido)

        if not resultado['permitido']:
            logger.warning(f"❌ Comentario bloqueado: {resultado['razon']}")
            try:
                from applications.usuarios.models import Usuario
                usuario = Usuario.objects.filter(documento=instance.autor.numero_documento).first()
                registrar_moderacion(
                    usuario=usuario,
                    tipo_contenido='texto',
                    resultado_moderacion=resultado,
                    contenido_texto=instance.contenido
                )
            except Exception:
                pass
            raise ValidationError({'contenido': f"Comentario bloqueado: {resultado['razon']}"})

        logger.info("✅ Comentario aprobado")


# ─────────────────────────────────────────────────────────────
# MENSAJES DE CHAT
# ─────────────────────────────────────────────────────────────

@receiver(pre_save, sender='chat.Mensaje')
def moderar_mensaje_chat(sender, instance, **kwargs):
    """
    Modera mensajes de chat antes de guardar.

    REGLAS:
    - Filtro local (palabras prohibidas) → SIEMPRE bloquea
    - OpenAI API → bloquea solo categorías graves
    - Error/rate-limit → bloquea (seguro por defecto)
    """
    if instance.pk is None and instance.contenido:
        logger.info("🔍 Moderando mensaje de chat")

        resultado = moderacion.moderar_texto(instance.contenido)

        if not resultado['permitido']:
            metodo = resultado.get('metodo', '')

            # Palabras prohibidas → bloquear siempre
            if metodo == 'filtro_local':
                logger.warning(f"❌ Mensaje bloqueado (filtro local): {resultado['razon']}")
                registrar_moderacion(
                    usuario=instance.autor,
                    tipo_contenido='texto',
                    resultado_moderacion=resultado,
                    contenido_texto=instance.contenido
                )
                raise ValidationError({'contenido': 'Mensaje bloqueado: usa un lenguaje respetuoso'})

            # OpenAI detectó algo grave
            elif metodo == 'openai_api':
                categorias_graves = [
                    'sexual', 'sexual/minors', 'violence/graphic',
                    'hate/threatening', 'self-harm/intent',
                    'harassment/threatening', 'illicit/violent'
                ]
                if any(cat in resultado.get('categorias_violadas', []) for cat in categorias_graves):
                    logger.warning(f"❌ Mensaje bloqueado (OpenAI): {resultado['razon']}")
                    registrar_moderacion(
                        usuario=instance.autor,
                        tipo_contenido='texto',
                        resultado_moderacion=resultado,
                        contenido_texto=instance.contenido
                    )
                    raise ValidationError({'contenido': 'Mensaje bloqueado por contenido inapropiado grave'})

            # Rate-limit o error → bloquear con mensaje amigable
            elif metodo in ('error_rate_limit', 'error_fallback'):
                logger.warning(f"❌ Mensaje bloqueado (servicio no disponible): {resultado['razon']}")
                raise ValidationError({'contenido': resultado['razon']})

        logger.info("✅ Mensaje aprobado")