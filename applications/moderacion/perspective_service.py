# applications/moderacion/perspective_service.py
"""
Servicio de moderación con Perspective API - VERSIÓN MEJORADA
- Umbrales más estrictos
- Mejor logging para debug
- Detecta variaciones leetspeak automáticamente (números, símbolos → letras)
- Filtro local corre SIEMPRE, no solo como fallback
"""

import logging
import unicodedata
import re
from typing import Dict
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PerspectiveModeration:
    """Moderación con Perspective API + filtro local leetspeak siempre activo"""

    # -----------------------------------------------------------------------
    # Mapa leetspeak: símbolo/número → letra equivalente
    # -----------------------------------------------------------------------
    LEET_MAP = {
        '0': 'o',
        '1': 'i',
        '2': 'z',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '6': 'g',
        '7': 't',
        '8': 'b',
        '9': 'g',
        '@': 'a',
        '$': 's',
        '!': 'i',
        '|': 'i',
        '+': 't',
        '(': 'c',
        '<': 'c',
        '[': 'c',
        '{': 'c',
        '€': 'e',
        '#': 'h',
        '%': 'o',
        '^': 'a',
    }

    def __init__(self):
        self.api_key = getattr(settings, 'PERSPECTIVE_API_KEY', '')

        self.thresholds = getattr(settings, 'PERSPECTIVE_THRESHOLDS', {
            'TOXICITY': 0.55,
            'SEVERE_TOXICITY': 0.50,
            'INSULT': 0.55,
            'PROFANITY': 0.55,
            'THREAT': 0.50,
            'IDENTITY_ATTACK': 0.50,
        })

        self.cache_timeout = getattr(settings, 'MODERACION_CACHE_TIMEOUT', 300)
        self.debug_mode = getattr(settings, 'PERSPECTIVE_DEBUG', False)

        # Lista de palabras prohibidas: primero settings, luego hardcoded
        self.palabras_prohibidas = getattr(settings, 'MODERACION_PALABRAS_PROHIBIDAS', [
            'puta', 'puto', 'mierda', 'verga', 'pendejo',
            'gonorrea', 'hijueputa', 'malparido', 'marica',
            'maricon', 'cabron', 'imbecil', 'estupido', 'pito',
            'pene', 'tetas', 'cuca', 'vagina', 'culo', 'tetranutra',
            'cacorro', 'sapo', 'zunga', 'valija', 'pirobo', 'pingo',
            'pato', 'pata', 'mamerto', 'lanpara', 'guisa', 'guaricha',
            # Abreviaciones
            'hp', 'hdp', 'mrda', 'pndj', 'pt', 'pto', 'pta', 'hpta', 'mka', 'mrka', 'mrd',
            'hpt'
        ])

        # Pre-normalizar la lista de palabras prohibidas (una sola vez)
        self._palabras_norm = [self._normalizar_leetspeak(p) for p in self.palabras_prohibidas]

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
            logger.info("✅ Perspective API inicializada")
            logger.info(f"📊 Umbrales configurados: {self.thresholds}")
            if self.debug_mode:
                logger.info("🐛 Modo DEBUG activado")
        except Exception as e:
            logger.error(f"❌ Error al inicializar Perspective API: {e}")
            self.client = None

    # -----------------------------------------------------------------------
    # Normalización leetspeak
    # -----------------------------------------------------------------------
    def _normalizar_leetspeak(self, texto: str) -> str:
        """
        Convierte leetspeak a texto plano para comparación:
          m13rd4  → mierda
          $4p0    → sapo
          v3rg@   → verga
          put@    → puta
        """
        texto = texto.lower()

        # 1. Sustituir leetspeak carácter a carácter
        texto = ''.join(self.LEET_MAP.get(c, c) for c in texto)

        # 2. Quitar tildes/acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

        # 3. Quitar todo lo que no sea letra
        texto = re.sub(r'[^a-z]', '', texto)

        return texto

    # -----------------------------------------------------------------------
    # Filtro local (leetspeak + palabras prohibidas)
    # SIEMPRE se ejecuta — no es solo fallback
    # -----------------------------------------------------------------------
    def _filtro_local(self, texto: str) -> Dict:
        """
        Busca palabras prohibidas en el texto normalizado (soporta leetspeak).
        Se llama SIEMPRE, antes de llegar a Perspective.
        """
        texto_norm = self._normalizar_leetspeak(texto)

        encontradas = [
            self.palabras_prohibidas[i]
            for i, palabra_norm in enumerate(self._palabras_norm)
            if palabra_norm in texto_norm
        ]

        bloqueado = bool(encontradas)

        if bloqueado:
            logger.warning(f"🚫 [FILTRO LOCAL] Bloqueado: {encontradas}")
            logger.warning(f"   Original  : '{texto[:100]}'")
            logger.warning(f"   Normalizado: '{texto_norm[:100]}'")

        return {
            'bloqueado': bloqueado,
            'categorias_detectadas': ['PROFANITY'] if bloqueado else [],
            'scores': {},
            'razon': f'Filtro local: {", ".join(encontradas)}' if bloqueado else '',
            'metodo': 'filtro_local',
            'score_maximo': 1.0 if bloqueado else 0.0,
        }

    # -----------------------------------------------------------------------
    # Punto de entrada principal
    # -----------------------------------------------------------------------
    def moderar_texto(self, texto: str) -> Dict:
        """
        Flujo de moderación:
          1. Filtro local leetspeak  → bloquea inmediatamente si detecta algo
          2. Perspective API          → análisis semántico/contextual
          3. Fallback filtro local    → si Perspective no está disponible

        Returns:
            {
                'bloqueado': bool,
                'scores': dict,
                'categorias_detectadas': list,
                'razon': str,
                'metodo': str,
                'score_maximo': float
            }
        """
        if not texto or not texto.strip():
            return {
                'bloqueado': False,
                'categorias_detectadas': [],
                'scores': {},
                'razon': '',
                'metodo': 'skip',
                'score_maximo': 0.0,
            }

        # ── PASO 1: Filtro local SIEMPRE (leetspeak) ──────────────────────
        resultado_local = self._filtro_local(texto)
        if resultado_local['bloqueado']:
            # Bloqueo inmediato, sin gastar cuota de Perspective
            return resultado_local

        # ── PASO 2: Perspective API (si está disponible) ───────────────────
        if not self.client:
            logger.warning("⚠️ Perspective API no disponible, solo filtro local aplicado")
            return resultado_local  # ya viene con bloqueado=False

        # Verificar caché
        cache_key = f'perspective_{hash(texto)}'
        cached = cache.get(cache_key)
        if cached:
            if self.debug_mode:
                logger.debug(f"📦 Caché hit: {texto[:30]}...")
            return cached

        try:
            analyze_request = {
                'comment': {'text': texto},
                'languages': ['es', 'en'],
                'requestedAttributes': {attr: {} for attr in self.thresholds.keys()},
            }

            logger.info(f"🔍 Perspective: '{texto[:50]}{'...' if len(texto) > 50 else ''}'")
            response = self.client.comments().analyze(body=analyze_request).execute()

            scores = {}
            categorias_detectadas = []
            score_maximo = 0.0

            for categoria, threshold in self.thresholds.items():
                try:
                    score = response['attributeScores'][categoria]['summaryScore']['value']
                    scores[categoria] = round(score, 3)
                    score_maximo = max(score_maximo, score)

                    if self.debug_mode:
                        status = "🔴" if score >= threshold else "🟢"
                        logger.info(f"   {status} {categoria}: {score:.3f} (umbral: {threshold})")

                    if score >= threshold:
                        categorias_detectadas.append(categoria)
                        logger.warning(f"   ⚠️ {categoria}: {score:.3f} >= {threshold} → BLOQUEADO")

                except KeyError:
                    if self.debug_mode:
                        logger.debug(f"   ℹ️ Categoría {categoria} no disponible")

            bloqueado = bool(categorias_detectadas)

            resultado = {
                'bloqueado': bloqueado,
                'scores': scores,
                'categorias_detectadas': categorias_detectadas,
                'razon': f'Contenido inapropiado: {", ".join(categorias_detectadas)}' if bloqueado else '',
                'metodo': 'perspective_api',
                'score_maximo': round(score_maximo, 3),
            }

            cache.set(cache_key, resultado, self.cache_timeout)

            if bloqueado:
                logger.warning(f"🚫 BLOQUEADO por Perspective (score máx: {score_maximo:.3f})")
                logger.warning(f"   Texto: '{texto[:100]}'")
                logger.warning(f"   Categorías: {categorias_detectadas}")
            else:
                logger.info(f"✅ APROBADO (score máx: {score_maximo:.3f})")

            return resultado

        except HttpError as e:
            logger.error(f"❌ Error HTTP en Perspective API: {e}")
            if e.resp.status == 429:
                logger.error("   → Rate limit excedido (429)")
            elif e.resp.status == 403:
                logger.error("   → Permiso denegado (403)")
            # Fallback: el filtro local ya se corrió y no bloqueó → permitir
            return resultado_local

        except Exception as e:
            logger.error(f"❌ Error inesperado en Perspective API: {e}")
            return resultado_local

    # -----------------------------------------------------------------------
    # Test de conexión
    # -----------------------------------------------------------------------
    def test_connection(self) -> bool:
        """Prueba la conexión con Perspective API"""
        if not self.client:
            logger.error("❌ Cliente de Perspective no inicializado")
            return False

        try:
            analyze_request = {
                'comment': {'text': 'Hello world'},
                'languages': ['en'],
                'requestedAttributes': {'TOXICITY': {}},
            }
            self.client.comments().analyze(body=analyze_request).execute()
            logger.info("✅ Conexión con Perspective API exitosa")
            return True
        except Exception as e:
            logger.error(f"❌ Error al probar conexión con Perspective: {e}")
            return False