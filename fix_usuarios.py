import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'info.settings')
django.setup()

from django.contrib.auth.models import User
from applications.usuarios.models import Usuario

def fix_users():
    users_fixed = 0
    
    for user in User.objects.all():
        try:
            _ = user.usuario
            print(f"✓ {user.username} ya tiene Usuario")
        except Usuario.DoesNotExist:
            Usuario.objects.create(
                user=user,
                tipo='aprendiz',
                documento=f'temp_{user.id}',
                nombre=user.username or user.email.split('@')[0],
                email=user.email or f'{user.username}@temp.com'
            )
            users_fixed += 1
            print(f"✓ Usuario creado para {user.username}")
    
    print(f"\n{users_fixed} usuarios arreglados")

if __name__ == '__main__':
    fix_users()