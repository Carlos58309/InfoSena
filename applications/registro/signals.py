# applications/registro/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
from django.contrib.auth.models import User

# ======================================
#  APRENDIZ → USUARIO
# ======================================
@receiver(post_save, sender=Aprendiz)
def sincronizar_aprendiz(sender, instance, created, **kwargs):
    # ⚠️ SOLO SINCRONIZAR SI ESTÁ VERIFICADO
    if not instance.verificado:
        print(f"⏸️ Aprendiz {instance.nombre} aún no verificado - Signal pausado")
        return
    
    if created or not Usuario.objects.filter(documento=instance.numero_documento).exists():
        # Crear usuario de Django
        user, user_created = User.objects.get_or_create(
            username=instance.email,
            defaults={'email': instance.email}
        )
        
        if user_created:
            user.set_password(instance.contrasena)
            user.save()
        
        # Crear registro en Usuario
        usuario, usuario_created = Usuario.objects.get_or_create(
            documento=instance.numero_documento,
            defaults={
                'user': user,
                'tipo': 'aprendiz',
                'nombre': instance.nombre,
                'email': instance.email,
                'foto': instance.foto if instance.foto else None
            }
        )
        
        print(f"{'✅ CREADO' if usuario_created else '⚠️ YA EXISTÍA'}: Usuario {usuario.nombre} - Doc: {usuario.documento}")
        
    else:
        # Actualizar usuario existente
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            usuario.nombre = instance.nombre
            usuario.email = instance.email
            if instance.foto:
                usuario.foto = instance.foto
            usuario.save()
            
            if usuario.user:
                usuario.user.email = instance.email
                usuario.user.save()
        except Usuario.DoesNotExist:
            pass


# ======================================
#  INSTRUCTOR → USUARIO
# ======================================
@receiver(post_save, sender=Instructor)
def sincronizar_instructor(sender, instance, created, **kwargs):
    # ⚠️ SOLO SINCRONIZAR SI ESTÁ VERIFICADO Y APROBADO
    if not instance.verificado or not instance.verificado_admin:
        print(f"⏸️ Instructor {instance.nombre} pendiente de verificación - Signal pausado")
        return
    
    if created or not Usuario.objects.filter(documento=instance.numero_documento).exists():
        user, user_created = User.objects.get_or_create(
            username=instance.email,
            defaults={'email': instance.email}
        )
        
        if user_created:
            user.set_password(instance.contrasena)
            user.save()
        
        usuario, usuario_created = Usuario.objects.get_or_create(
            documento=instance.numero_documento,
            defaults={
                'user': user,
                'tipo': 'instructor',
                'nombre': instance.nombre,
                'email': instance.email,
                'foto': instance.foto if instance.foto else None
            }
        )
        
        print(f"{'✅ CREADO' if usuario_created else '⚠️ YA EXISTÍA'}: Usuario {usuario.nombre} - Doc: {usuario.documento}")
        
    else:
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            usuario.nombre = instance.nombre
            usuario.email = instance.email
            if instance.foto:
                usuario.foto = instance.foto
            usuario.save()
            
            if usuario.user:
                usuario.user.email = instance.email
                usuario.user.save()
        except Usuario.DoesNotExist:
            pass


# ======================================
#  BIENESTAR → USUARIO
# ======================================
@receiver(post_save, sender=Bienestar)
def sincronizar_bienestar(sender, instance, created, **kwargs):
    # ⚠️ SOLO SINCRONIZAR SI ESTÁ VERIFICADO Y APROBADO
    if not instance.verificado or not instance.verificado_admin:
        print(f"⏸️ Bienestar {instance.nombre} pendiente de verificación - Signal pausado")
        return
    
    if created or not Usuario.objects.filter(documento=instance.numero_documento).exists():
        user, user_created = User.objects.get_or_create(
            username=instance.email,
            defaults={'email': instance.email}
        )
        
        if user_created:
            user.set_password(instance.contrasena)
            user.save()
        
        usuario, usuario_created = Usuario.objects.get_or_create(
            documento=instance.numero_documento,
            defaults={
                'user': user,
                'tipo': 'bienestar',
                'nombre': instance.nombre,
                'email': instance.email,
                'foto': instance.foto if instance.foto else None
            }
        )
        
        print(f"{'✅ CREADO' if usuario_created else '⚠️ YA EXISTÍA'}: Usuario {usuario.nombre} - Doc: {usuario.documento}")
        
    else:
        try:
            usuario = Usuario.objects.get(documento=instance.numero_documento)
            usuario.nombre = instance.nombre
            usuario.email = instance.email
            if instance.foto:
                usuario.foto = instance.foto
            usuario.save()
            
            if usuario.user:
                usuario.user.email = instance.email
                usuario.user.save()
        except Usuario.DoesNotExist:
            pass


# ======================================
#  USUARIO → TABLAS ORIGINALES
# ======================================
@receiver(post_save, sender=Usuario)
def actualizar_tabla_original(sender, instance, created, **kwargs):
    """Sincroniza cambios de Usuario hacia las tablas originales"""
    if not created:
        try:
            if instance.tipo == 'aprendiz':
                aprendiz = Aprendiz.objects.get(numero_documento=instance.documento)
                aprendiz.nombre = instance.nombre
                aprendiz.email = instance.email
                if instance.foto:
                    aprendiz.foto = instance.foto
                aprendiz.save()
                
            elif instance.tipo == 'instructor':
                instructor = Instructor.objects.get(numero_documento=instance.documento)
                instructor.nombre = instance.nombre
                instructor.email = instance.email
                if instance.foto:
                    instructor.foto = instance.foto
                instructor.save()
                
            elif instance.tipo == 'bienestar':
                bienestar = Bienestar.objects.get(numero_documento=instance.documento)
                bienestar.nombre = instance.nombre
                bienestar.email = instance.email
                if instance.foto:
                    bienestar.foto = instance.foto
                bienestar.save()
        except Exception as e:
            print(f"Error sincronizando usuario a tabla original: {e}")


# ======================================
#  ELIMINAR EN CASCADA
# ======================================
@receiver(post_delete, sender=Aprendiz)
def eliminar_usuario_aprendiz(sender, instance, **kwargs):
    try:
        usuario = Usuario.objects.get(documento=instance.numero_documento)
        if usuario.user:
            usuario.user.delete()
        usuario.delete()
    except Usuario.DoesNotExist:
        pass


@receiver(post_delete, sender=Instructor)
def eliminar_usuario_instructor(sender, instance, **kwargs):
    try:
        usuario = Usuario.objects.get(documento=instance.numero_documento)
        if usuario.user:
            usuario.user.delete()
        usuario.delete()
    except Usuario.DoesNotExist:
        pass


@receiver(post_delete, sender=Bienestar)
def eliminar_usuario_bienestar(sender, instance, **kwargs):
    try:
        usuario = Usuario.objects.get(documento=instance.numero_documento)
        if usuario.user:
            usuario.user.delete()
        usuario.delete()
    except Usuario.DoesNotExist:
        pass