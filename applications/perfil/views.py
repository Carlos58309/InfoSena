# perfil/views.py
from django.shortcuts import render, redirect, get_object_or_404
from applications.registro.models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
import os
from django.conf import settings
from django.core.files.storage import default_storage



@login_required
def perfil(request):
    """
    Vista para mostrar el perfil del usuario logueado
    Usando sistema de autenticación personalizado
    """
    # Verificar si hay una sesión activa
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    tipo_perfil = request.session['tipo_usuario']
    datos_usuario = None
    
    # Buscar el usuario según su tipo
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        return redirect('perfil:perfiles')
    
    # Preparar el contexto para el template
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
    }
    return render(request, 'perfil.html', context)

def dashboard_view(request):
    return render(request, "home.html")


@login_required
def editar_perfil(request):
    # Verificar sesión
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')
    
    usuario_id = request.session['usuario_id']
    tipo_perfil = request.session['tipo_usuario']
    datos_usuario = None
    
    # Obtener el perfil según tipo
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        messages.error(request, "Usuario no encontrado")
        return redirect('perfil:perfiles')
    
    if request.method == 'POST':
        # Actualizar campos básicos
        datos_usuario.nombre = request.POST.get('nombre')
        datos_usuario.email = request.POST.get('email')
        datos_usuario.tipo_documento = request.POST.get('tipo_documento')
        datos_usuario.centro_formativo = request.POST.get('centro_formativo')
        datos_usuario.region = request.POST.get('region')

        # Si es aprendiz tiene atributos extra
        if tipo_perfil == 'aprendiz':
            datos_usuario.ficha = request.POST.get('ficha')
            datos_usuario.jornada = request.POST.get('jornada')

        # =========================
        #     MANEJO DE FOTO - CORREGIDO
        # =========================
        foto_nueva = request.FILES.get('foto')
        
        print("=" * 50)
        print("DEBUG - Información de la foto:")
        print(f"FILES completo: {request.FILES}")
        print(f"foto_nueva: {foto_nueva}")
        if foto_nueva:
            print(f"Nombre del archivo: {foto_nueva.name}")
            print(f"Tamaño: {foto_nueva.size} bytes")
            print(f"Content-type: {foto_nueva.content_type}")
        print("=" * 50)

        if foto_nueva:
            # Eliminar foto vieja si existe
            if datos_usuario.foto:
                try:
                    # Usar el storage de Django para eliminar
                    if default_storage.exists(datos_usuario.foto.name):
                        default_storage.delete(datos_usuario.foto.name)
                        print(f"✓ Foto antigua eliminada: {datos_usuario.foto.name}")
                except Exception as e:
                    print(f"⚠ Error al eliminar foto antigua: {e}")

            # Guardar nueva foto
            datos_usuario.foto = foto_nueva
            print(f"✓ Nueva foto asignada: {foto_nueva.name}")

        # Guardar todos los cambios
        try:
            datos_usuario.save()
            print("✓ Usuario guardado correctamente en la base de datos")
            
            # Verificar que se guardó
            if tipo_perfil == 'aprendiz':
                verificacion = Aprendiz.objects.get(numero_documento=usuario_id)
            elif tipo_perfil == 'instructor':
                verificacion = Instructor.objects.get(numero_documento=usuario_id)
            elif tipo_perfil == 'bienestar':
                verificacion = Bienestar.objects.get(numero_documento=usuario_id)
            
            print(f"✓ Verificación - Foto en BD: {verificacion.foto}")
            
            messages.success(request, "Perfil actualizado correctamente")
        except Exception as e:
            print(f"✗ Error al guardar: {e}")
            messages.error(request, f"Error al guardar el perfil: {str(e)}")
        
        return redirect('perfil:perfiles')
    
    context = {'usuario': datos_usuario, 'tipo_perfil': tipo_perfil}
    return render(request, 'editar_perfil.html', context)



@login_required
def eliminar_perfil(request):
    if request.method == 'POST':
        if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
            return redirect('sesion:login')

        usuario_id = request.session['usuario_id']
        tipo_perfil = request.session['tipo_usuario']
        datos_usuario = None

        try:
            if tipo_perfil == 'aprendiz':
                datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
            elif tipo_perfil == 'instructor':
                datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
            elif tipo_perfil == 'bienestar':
                datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
            messages.error(request, "Usuario no encontrado")
            return redirect('perfil:perfiles')

        # Borrar sesión y el objeto
        logout(request)
        datos_usuario.delete()
        messages.success(request, "Cuenta eliminada correctamente")
        return redirect('home')

    return render(request, 'eliminar_perfil.html')


@login_required
def ver_perfil(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Verificar si es el perfil del usuario actual
    es_perfil_propio = request.user.id == usuario_id
    
    context = {
        'usuario': usuario,
        'es_perfil_propio': es_perfil_propio,
    }
    
    return render(request, 'ver_perfil.html', context)