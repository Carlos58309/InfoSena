from django.core.management.base import BaseCommand
from applications.registro.models import Aprendiz
from applications.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea un usuario administrador inicial'

    def handle(self, *args, **kwargs):
        documento = '00000001'
        email = 'admin@infosena.com'

        if Aprendiz.objects.filter(numero_documento=documento).exists():
            self.stdout.write(self.style.WARNING('El usuario admin ya existe.'))
            return

        Aprendiz.objects.create(
            numero_documento=documento,
            nombre='Administrador',
            tipo_documento='CC',
            email=email,
            centro_formativo='SENA',
            region='Nacional',
            jornada='Diurna',
            ficha='000000',
            contrasena='Admin2024@',
            verificado=True,
        )

        Usuario.objects.create(
            documento=documento,
            nombre='Administrador',
            tipo='aprendiz',
            email=email,
            es_admin=True,
        )

        self.stdout.write(self.style.SUCCESS(
            'Admin creado. Documento: 00000001 | Contraseña: Admin2024@'
        ))
