# applications/moderacion/apps.py

from django.apps import AppConfig


class ModeracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.moderacion'
    verbose_name = 'Sistema de Moderación IA'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import applications.moderacion.signals

