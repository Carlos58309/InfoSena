# applications/moderacion/moderacion_service.py
"""
Servicio centralizado de moderación de contenido usando OpenAI Moderation API
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ModeracionService:
    """
    Servicio para moderar contenido de texto, imágenes y videos usando OpenAI
    """

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.model = getattr(settings, 'OPENAI_MODERATION_MODEL', 'omni-moderation-latest')
        self.cache_timeout = getattr(settings, 'MODERACION_CACHE_TIMEOUT', 300)

        self.max_texto_length = getattr(settings, 'MODERACION_MAX_TEXTO_LENGTH', 5000)
        self.max_image_size = getattr(settings, 'MODERACION_MAX_IMAGE_SIZE', 10 * 1024 * 1024)
        self.max_video_size = getattr(settings, 'MODERACION_MAX_VIDEO_SIZE', 50 * 1024 * 1024)

        self.categorias_bloqueadas = getattr(settings, 'MODERACION_CATEGORIAS_BLOQUEADAS', [
            'sexual', 'sexual/minors', 'violence', 'violence/graphic',
            'harassment', 'harassment/threatening', 'hate', 'hate/threatening',
            'self-harm', 'self-harm/intent', 'self-harm/instructions',
            'illicit', 'illicit/violent'
        ])

        self.palabras_prohibidas = self._cargar_palabras_prohibidas()

    def _cargar_palabras_prohibidas(self) -> List[str]:
        """Carga lista de palabras prohibidas desde settings"""
        # Primero intenta cargar desde la base de datos
        try:
            from .models import PalabraProhibida
            palabras_db = list(
                PalabraProhibida.objects.filter(activa=True).values_list('palabra', flat=True)
            )
            if palabras_db:
                return [p.lower() for p in palabras_db]
        except Exception:
            pass

        # Fallback a settings
        palabras = getattr(settings, 'MODERACION_PALABRAS_PROHIBIDAS', [
            'puta', 'puto', 'cabrón', 'cabron', 'mierda', 'verga', 'pendejo',
            'gonorrea', 'hijueputa', 'malparido', 'marica', 'maricon',
            'idiota', 'imbecil', 'estupido', 'estúpido', 'hdp',
        ])
        return [p.lower() for p in palabras]

    def verificar_api_key(self) -> bool:
        """Verifica si la API key está configurada"""
        if not self.api_key:
            logger.error("⚠️ OPENAI_API_KEY no configurada en settings")
            return False
        return True

    def moderar_texto(self, texto: str, usar_cache: bool = True) -> Dict:
        """
        Modera un texto. Retorna siempre:
        {
            'permitido': bool,
            'bloqueado': bool,   ← alias de not permitido (para compatibilidad)
            'razon': str,
            'categorias_violadas': list,
            'metodo': str
        }
        """
        if not texto or not texto.strip():
            return {'permitido': True, 'bloqueado': False, 'razon': 'Texto vacío', 'metodo': 'sin_verificacion'}

        # Validar longitud
        if len(texto) > self.max_texto_length:
            return {
                'permitido': False,
                'bloqueado': True,
                'razon': f'El texto excede el límite de {self.max_texto_length} caracteres',
                'categorias_violadas': ['longitud_excedida'],
                'metodo': 'validacion_local'
            }

        # Verificar cache
        cache_key = f"moderacion_v2_{hash(texto)}"
        if usar_cache:
            resultado_cache = cache.get(cache_key)
            if resultado_cache:
                logger.info("✅ Resultado de moderación obtenido del caché")
                return resultado_cache

        # ─── FILTRO LOCAL (siempre se ejecuta primero) ───────────────────────
        palabras_encontradas = self._detectar_palabras_prohibidas(texto)
        if palabras_encontradas:
            resultado = {
                'permitido': False,
                'bloqueado': True,
                'razon': 'Contenido inapropiado detectado (palabras prohibidas)',
                'categorias_violadas': ['lenguaje_ofensivo'],
                'palabras_detectadas': palabras_encontradas,
                'metodo': 'filtro_local'
            }
            if usar_cache:
                cache.set(cache_key, resultado, self.cache_timeout)
            return resultado

        # ─── API OPENAI ────────────────────────────────────────────────────
        if not self.verificar_api_key():
            # Sin API key → confiar en filtro local (ya pasó)
            return {
                'permitido': True,
                'bloqueado': False,
                'razon': 'API no disponible, filtro local pasado',
                'categorias_violadas': [],
                'metodo': 'filtro_local_fallback'
            }

        try:
            import openai
            openai.api_key = self.api_key

            # Reintentos ante rate-limit (429)
            max_intentos = 3
            for intento in range(max_intentos):
                try:
                    response = openai.moderations.create(
                        model=self.model,
                        input=texto
                    )
                    break
                except openai.RateLimitError:
                    if intento < max_intentos - 1:
                        wait = 2 ** intento  # 1s, 2s, 4s
                        logger.warning(f"⚠️ Rate limit OpenAI, reintentando en {wait}s...")
                        time.sleep(wait)
                    else:
                        # Agotados los reintentos → bloquear por precaución
                        logger.error("❌ Rate limit agotado en OpenAI. Bloqueando por precaución.")
                        resultado = {
                            'permitido': False,
                            'bloqueado': True,
                            'razon': 'Servicio de moderación temporalmente no disponible. Inténtalo de nuevo.',
                            'categorias_violadas': [],
                            'metodo': 'error_rate_limit'
                        }
                        # Cache corto para no bloquear demasiado tiempo
                        if usar_cache:
                            cache.set(cache_key, resultado, 30)
                        return resultado

            resultado_api = response.results[0]

            categorias_violadas = [
                categoria
                for categoria, violado in resultado_api.categories.model_dump().items()
                if violado and categoria in self.categorias_bloqueadas
            ]

            permitido = not resultado_api.flagged
            resultado = {
                'permitido': permitido,
                'bloqueado': not permitido,
                'razon': 'Contenido apropiado' if permitido else 'Contenido inapropiado detectado por IA',
                'categorias_violadas': categorias_violadas,
                'score_confianza': resultado_api.category_scores.model_dump(),
                'metodo': 'openai_api'
            }

            if usar_cache:
                cache.set(cache_key, resultado, self.cache_timeout)

            logger.info(f"{'✅' if permitido else '❌'} Moderación texto: {resultado['razon']}")
            return resultado

        except Exception as e:
            logger.error(f"❌ Error inesperado en moderación: {str(e)}")
            # Ante error desconocido → BLOQUEAR (seguro por defecto)
            return {
                'permitido': False,
                'bloqueado': True,
                'razon': 'Error en el servicio de moderación. Inténtalo de nuevo.',
                'categorias_violadas': [],
                'error': str(e),
                'metodo': 'error_fallback'
            }

    def moderar_imagen(self, imagen_url: str = None, imagen_base64: str = None) -> Dict:
        """Modera una imagen usando OpenAI Moderation API"""
        if not imagen_url and not imagen_base64:
            return {'permitido': True, 'bloqueado': False, 'razon': 'Sin imagen para moderar'}

        if not self.verificar_api_key():
            return {
                'permitido': True,
                'bloqueado': False,
                'razon': 'API no disponible para imágenes',
                'metodo': 'sin_verificacion'
            }

        try:
            import openai
            openai.api_key = self.api_key

            if imagen_url:
                input_data = [{"type": "image_url", "image_url": {"url": imagen_url}}]
            else:
                input_data = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"}}]

            response = openai.moderations.create(model=self.model, input=input_data)
            resultado_api = response.results[0]

            categorias_violadas = [
                categoria
                for categoria, violado in resultado_api.categories.model_dump().items()
                if violado and categoria in self.categorias_bloqueadas
            ]

            permitido = not resultado_api.flagged
            resultado = {
                'permitido': permitido,
                'bloqueado': not permitido,
                'razon': 'Imagen apropiada' if permitido else 'Imagen inapropiada detectada',
                'categorias_violadas': categorias_violadas,
                'metodo': 'openai_api'
            }

            logger.info(f"{'✅' if permitido else '❌'} Moderación imagen: {resultado['razon']}")
            return resultado

        except Exception as e:
            logger.error(f"❌ Error en moderación de imagen: {str(e)}")
            return {
                'permitido': True,
                'bloqueado': False,
                'razon': f'Error en API de imágenes: {str(e)}',
                'error': str(e),
                'metodo': 'error_fallback'
            }

    def moderar_archivo(self, archivo) -> Dict:
        """Modera un archivo (imagen o video)"""
        if archivo.size > self.max_image_size and 'image' in archivo.content_type:
            return {
                'permitido': False,
                'bloqueado': True,
                'razon': f'Imagen excede el tamaño máximo de {self.max_image_size / (1024*1024)}MB'
            }

        if archivo.size > self.max_video_size and 'video' in archivo.content_type:
            return {
                'permitido': False,
                'bloqueado': True,
                'razon': f'Video excede el tamaño máximo de {self.max_video_size / (1024*1024)}MB'
            }

        if 'image' in archivo.content_type:
            import base64
            try:
                archivo.seek(0)
                imagen_base64 = base64.b64encode(archivo.read()).decode('utf-8')
                return self.moderar_imagen(imagen_base64=imagen_base64)
            except Exception as e:
                logger.error(f"Error convirtiendo imagen a base64: {e}")
                return {'permitido': True, 'bloqueado': False, 'razon': 'Error procesando imagen', 'error': str(e)}

        return {'permitido': True, 'bloqueado': False, 'razon': 'Video validado por tamaño', 'metodo': 'validacion_basica'}

    def moderar_contenido_completo(self, texto: str = None, archivos: List = None) -> Tuple[bool, List[str]]:
        """Modera texto y archivos juntos. Retorna (permitido, errores)"""
        errores = []

        if texto:
            resultado_texto = self.moderar_texto(texto)
            if not resultado_texto['permitido']:
                errores.append(resultado_texto['razon'])

        if archivos:
            for i, archivo in enumerate(archivos):
                resultado_archivo = self.moderar_archivo(archivo)
                if not resultado_archivo['permitido']:
                    errores.append(f"Archivo {i+1}: {resultado_archivo['razon']}")

        return (len(errores) == 0, errores)

    def _detectar_palabras_prohibidas(self, texto: str) -> List[str]:
        """Detecta palabras prohibidas en el texto (filtro local rápido)"""
        import unicodedata
        # Normalizar: quitar acentos para detectar variantes (e.g. "estúpido" → "estupido")
        texto_normalizado = unicodedata.normalize('NFD', texto.lower())
        texto_normalizado = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')

        palabras_encontradas = []
        for palabra in self.palabras_prohibidas:
            palabra_normalizada = unicodedata.normalize('NFD', palabra.lower())
            palabra_normalizada = ''.join(c for c in palabra_normalizada if unicodedata.category(c) != 'Mn')
            if palabra_normalizada in texto_normalizado:
                palabras_encontradas.append(palabra)

        return palabras_encontradas

    def validar_nombre_usuario(self, nombre: str) -> Dict:
        """Valida que un nombre de usuario sea apropiado"""
        if not nombre or len(nombre) < 3:
            return {'permitido': False, 'bloqueado': True, 'razon': 'El nombre debe tener al menos 3 caracteres'}
        if len(nombre) > 50:
            return {'permitido': False, 'bloqueado': True, 'razon': 'El nombre no puede exceder 50 caracteres'}
        return self.moderar_texto(nombre, usar_cache=False)

    def validar_biografia(self, biografia: str) -> Dict:
        """Valida que una biografía sea apropiada"""
        if len(biografia) > 500:
            return {'permitido': False, 'bloqueado': True, 'razon': 'La biografía no puede exceder 500 caracteres'}
        return self.moderar_texto(biografia)


# Instancia global del servicio
moderacion = ModeracionService()