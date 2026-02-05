from django.apps import AppConfig

class PerfilConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.notificaciones'
    def ready(self):
        import applications.notificaciones.signals