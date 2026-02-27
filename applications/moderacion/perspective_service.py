# applications/moderacion/perspective_service.py
"""
Servicio de moderación con Perspective API de Google
- 1M requests/día GRATIS
- Detecta automáticamente variaciones (mierda, mrda, m1erd4)
- Sin rate limits molestos
"""

import logging
from typing import Dict
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PerspectiveModeration:
    """Moderación con Perspective API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'PERSPECTIVE_API_KEY', '')
        self.thresholds = getattr(settings, 'PERSPECTIVE_THRESHOLDS', {
            'TOXICITY': 0.7,
            'SEVERE_TOXICITY': 0.6,
            'INSULT': 0.7,
            'PROFANITY': 0.7,
            'THREAT': 0.6,
            'IDENTITY_ATTACK': 0.7
        })
        self.cache_timeout = getattr(settings, 'MODERACION_CACHE_TIMEOUT', 300)
        
        if not self.api_key:
            logger.error("❌ PERSPECTIVE_API_KEY no configurada en settings.py")
            self.client = None
            return
        
        try:
            self.client = discovery.build(
                "commentanalyzer",
                "v1alpha1",
                developerKey=self.api_key,
                discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                static_discovery=False
            )
            logger.info("✅ Perspective API inicializada correctamente")
            logger.info(f"📊 Umbrales configurados: {self.thresholds}")
        except Exception as e:
            logger.error(f"❌ Error al inicializar Perspective API: {e}")
            self.client = None
    
    def moderar_texto(self, texto: str) -> Dict:
        """
        Modera texto usando Perspective API
        
        Args:
            texto: Texto a moderar
            
        Returns:
            {
                'bloqueado': bool,
                'scores': dict,
                'categorias_detectadas': list,
                'razon': str,
                'metodo': str
            }
        """
        # Validar entrada
        if not texto or not texto.strip():
            return {
                'bloqueado': False,
                'categorias_detectadas': [],
                'scores': {},
                'razon': '',
                'metodo': 'skip'
            }
        
        # Si no hay cliente, usar fallback
        if not self.client:
            logger.warning("⚠️ Perspective API no disponible, usando filtro local")
            return self._filtro_local_fallback(texto)
        
        # Verificar caché
        cache_key = f'perspective_{hash(texto)}'
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"📦 Caché hit para: {texto[:30]}...")
            return cached
        
        try:
            # Preparar request
            analyze_request = {
                'comment': {'text': texto},
                'languages': ['es', 'en'],  # Español e inglés
                'requestedAttributes': {
                    attr: {} for attr in self.thresholds.keys()
                }
            }
            
            # Llamar a Perspective API
            logger.info(f"🔍 Moderando con Perspective: {texto[:50]}...")
            response = self.client.comments().analyze(body=analyze_request).execute()
            
            # Procesar resultados
            scores = {}
            categorias_detectadas = []
            
            for categoria, threshold in self.thresholds.items():
                try:
                    score = response['attributeScores'][categoria]['summaryScore']['value']
                    scores[categoria] = round(score, 3)
                    
                    if score >= threshold:
                        categorias_detectadas.append(categoria)
                        logger.warning(f"   ⚠️ {categoria}: {score:.3f} >= {threshold}")
                    else:
                        logger.debug(f"   ✓ {categoria}: {score:.3f} < {threshold}")
                        
                except KeyError:
                    logger.debug(f"   ℹ️ Categoría {categoria} no disponible en respuesta")
            
            bloqueado = len(categorias_detectadas) > 0
            
            resultado = {
                'bloqueado': bloqueado,
                'scores': scores,
                'categorias_detectadas': categorias_detectadas,
                'razon': f'Contenido inapropiado: {", ".join(categorias_detectadas)}' if bloqueado else '',
                'metodo': 'perspective_api'
            }
            
            # Guardar en caché
            cache.set(cache_key, resultado, self.cache_timeout)
            
            # Log del resultado
            if bloqueado:
                logger.warning(f"🚫 BLOQUEADO por Perspective")
                logger.warning(f"   Texto: {texto[:100]}")
                logger.warning(f"   Categorías: {categorias_detectadas}")
            else:
                logger.info(f"✅ APROBADO por Perspective")
                logger.info(f"   Texto: {texto[:100]}")
            
            return resultado
            
        except HttpError as e:
            # Errores HTTP de Google (rate limit, permisos, etc.)
            logger.error(f"❌ Error HTTP en Perspective API: {e}")
            
            if e.resp.status == 429:
                logger.error("   → Rate limit excedido (429)")
            elif e.resp.status == 403:
                logger.error("   → Permiso denegado (403) - Verifica que la API esté habilitada")
            
            return self._filtro_local_fallback(texto)
            
        except Exception as e:
            # Otros errores
            logger.error(f"❌ Error inesperado en Perspective API: {e}")
            return self._filtro_local_fallback(texto)
    
    def _filtro_local_fallback(self, texto: str) -> Dict:
        """
        Filtro local cuando Perspective falla
        Busca palabras prohibidas básicas
        """
        palabras_prohibidas = [
            'puta', 'puto', 'mierda', 'verga', 'pendejo',
            'gonorrea', 'hijueputa', 'malparido', 'marica',
            'maricon', 'cabron', 'imbecil', 'estupido'
        ]
        
        # Normalizar texto
        import unicodedata
        texto_norm = texto.lower()
        texto_norm = unicodedata.normalize('NFD', texto_norm)
        texto_norm = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
        
        # Buscar palabras
        encontradas = []
        for palabra in palabras_prohibidas:
            palabra_norm = unicodedata.normalize('NFD', palabra.lower())
            palabra_norm = ''.join(c for c in palabra_norm if unicodedata.category(c) != 'Mn')
            
            if palabra_norm in texto_norm:
                encontradas.append(palabra)
        
        bloqueado = len(encontradas) > 0
        
        if bloqueado:
            logger.warning(f"🚫 Bloqueado por filtro local: {encontradas}")
        
        return {
            'bloqueado': bloqueado,
            'categorias_detectadas': ['PROFANITY'] if bloqueado else [],
            'scores': {},
            'razon': f'Filtro local: {", ".join(encontradas)}' if bloqueado else '',
            'metodo': 'filtro_local_fallback'
        }
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Perspective API
        Retorna True si funciona correctamente
        """
        if not self.client:
            logger.error("❌ Cliente de Perspective no inicializado")
            return False
        
        try:
            # Hacer una prueba simple
            test_text = "Hello world"
            analyze_request = {
                'comment': {'text': test_text},
                'languages': ['en'],
                'requestedAttributes': {'TOXICITY': {}}
            }
            
            response = self.client.comments().analyze(body=analyze_request).execute()
            logger.info("✅ Conexión con Perspective API exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al probar conexión con Perspective: {e}")
            return False