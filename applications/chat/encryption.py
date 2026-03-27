# applications/chat/encryption.py
import os
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)

def _get_fernet() -> Fernet:
    key = os.environ.get("CHAT_ENCRYPTION_KEY")
    if not key:
        raise EnvironmentError(
            "CHAT_ENCRYPTION_KEY no está definida en las variables de entorno. "
            "Agrégala en Railway > Variables."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encriptar(texto: str) -> str:
    """Encripta texto plano. Retorna string base64 seguro para guardar en BD."""
    if not texto:
        return texto
    try:
        return _get_fernet().encrypt(texto.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Error al encriptar mensaje: {e}")
        raise


def desencriptar(texto: str) -> str:
    """
    Desencripta un texto cifrado con Fernet.
    Si el texto NO está encriptado (mensajes viejos en texto plano),
    lo retorna tal cual para retrocompatibilidad.
    """
    if not texto:
        return texto
    try:
        return _get_fernet().decrypt(texto.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Mensaje antiguo en texto plano — se retorna sin cambios
        logger.debug("Mensaje no encriptado encontrado (retrocompatibilidad).")
        return texto
    except Exception as e:
        logger.error(f"Error al desencriptar mensaje: {e}")
        return texto  # En producción es mejor mostrar el texto tal cual que crashear