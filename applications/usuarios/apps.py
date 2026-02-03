from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.usuarios'
    def ready(self):
        import applications.usuarios.signals
