# perfil/views.py
from django.shortcuts import render, redirect
from applications.registro.models import Aprendiz, Instructor, Bienestar
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout



@login_required
def perfil(request):
    """
    Vista para mostrar el perfil del usuario logueado
    Usando sistema de autenticación personalizado
    """
    # Verificar si hay una sesión activa
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')  # Ajusta según tu URL de login
    
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
    # Si el usuario no tiene sesión, redirige al login
    return render(request, "home.html")



# parte de editar

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
        
        # Tipo de documento
        datos_usuario.tipo_documento = request.POST.get('tipo_documento')
        
        if tipo_perfil != 'aprendiz':  # si tiene centro_formativo y region
            datos_usuario.centro_formativo = request.POST.get('centro_formativo')
            datos_usuario.region = request.POST.get('region')
        else:  # aprendiz
            datos_usuario.centro_formativo = request.POST.get('centro_formativo')
            datos_usuario.region = request.POST.get('region')
            datos_usuario.ficha = request.POST.get('ficha')
            datos_usuario.jornada = request.POST.get('jornada')

        datos_usuario.save()
        messages.success(request, "Perfil actualizado correctamente")
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

        # Obtener el objeto según el tipo
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
        return redirect('home')  # o la página que quieras

    return render(request, 'eliminar_perfil.html')