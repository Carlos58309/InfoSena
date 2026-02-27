# applications/moderacion/moderacion_service.py
"""
Servicio principal de moderación
- Texto: Perspective API (Google) - Ilimitado y gratis
- Imágenes: OpenAI (opcional) - Solo si es necesario
"""

import logging
from typing import Dict
from django.conf import settings
from applications.moderacion.perspective_service import PerspectiveModeration

logger = logging.getLogger(__name__)


class ModeracionService:
    """Servicio de moderación con Perspective API"""
    
    def __init__(self):
        # Perspective para texto
        self.perspective = PerspectiveModeration()
        
        # OpenAI para imágenes (opcional)
        self.openai_client = None
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self.openai_model = 'omni-moderation-latest'
                logger.info("✅ OpenAI configurado para moderación de imágenes")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI no disponible: {e}")
        
        logger.info("🤖 ModeracionService iniciado")
        
        # Probar conexión con Perspective
        if self.perspective.client:
            logger.info("   → Perspective API: ACTIVA")
        else:
            logger.warning("   → Perspective API: INACTIVA (usando fallback)")
    
    def moderar_texto(self, texto: str) -> Dict:
        """
        Modera texto usando Perspective API
        
        Returns:
            {
                'bloqueado': bool,
                'categorias_detectadas': list,
                'scores': dict,
                'razon': str,
                'metodo': str
            }
        """
        return self.perspective.moderar_texto(texto)
    
    def moderar_imagen(self, imagen_url: str) -> Dict:
        """
        Modera imagen usando OpenAI (opcional)
        Las imágenes se suben menos frecuente, no hay problema con rate limit
        """
        if not self.openai_client:
            logger.info("ℹ️ Moderación de imágenes no configurada, permitiendo imagen")
            return {
                'bloqueado': False,
                'categorias_detectadas': [],
                'scores': {},
                'razon': '',
                'metodo': 'skip'
            }
        
        try:
            logger.info(f"🖼️ Moderando imagen con OpenAI: {imagen_url[:50]}...")
            
            response = self.openai_client.moderations.create(
                model=self.openai_model,
                input=[{
                    "type": "image_url",
                    "image_url": {"url": imagen_url}
                }]
            )
            
            result = response.results[0]
            categorias_detectadas = [
                cat for cat, flagged in result.categories.model_dump().items()
                if flagged
            ]
            
            bloqueado = len(categorias_detectadas) > 0
            
            if bloqueado:
                logger.warning(f"🚫 Imagen bloqueada: {categorias_detectadas}")
            else:
                logger.info("✅ Imagen aprobada")
            
            return {
                'bloqueado': bloqueado,
                'categorias_detectadas': categorias_detectadas,
                'scores': result.category_scores.model_dump(),
                'razon': f'Contenido inapropiado en imagen: {", ".join(categorias_detectadas)}' if bloqueado else '',
                'metodo': 'openai'
            }
            
        except Exception as e:
            logger.error(f"❌ Error al moderar imagen: {e}")
            # Por seguridad, bloquear si hay error
            return {
                'bloqueado': True,
                'categorias_detectadas': ['unknown'],
                'scores': {},
                'razon': 'Error al moderar imagen - bloqueado por seguridad',
                'metodo': 'error_fallback'
            }
    
    def moderar_archivo(self, archivo) -> Dict:
        """
        Modera archivos (imágenes y videos)
        Por ahora solo valida el tipo de archivo
        """
        logger.info(f"📄 Validando archivo: {archivo.name}")
        
        # Aquí puedes agregar validaciones adicionales
        # Por ejemplo: tamaño máximo, tipos permitidos, etc.
        
        return {
            'bloqueado': False,
            'categorias_detectadas': [],
            'scores': {},
            'razon': '',
            'metodo': 'skip'
        }
    
    def test_service(self) -> Dict:
        """
        Prueba el servicio de moderación
        Útil para verificar que todo esté configurado correctamente
        """
        resultados = {
            'perspective_api': False,
            'openai_api': False,
            'errores': []
        }
        
        # Probar Perspective
        try:
            if self.perspective.test_connection():
                resultados['perspective_api'] = True
            else:
                resultados['errores'].append('Perspective API no responde')
        except Exception as e:
            resultados['errores'].append(f'Error en Perspective: {str(e)}')
        
        # Probar OpenAI (opcional)
        if self.openai_client:
            try:
                # Hacer una prueba simple
                test_result = self.moderar_texto("test")
                if test_result:
                    resultados['openai_api'] = True
            except Exception as e:
                resultados['errores'].append(f'Error en OpenAI: {str(e)}')
        
        return resultados