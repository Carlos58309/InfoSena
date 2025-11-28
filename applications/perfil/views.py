# perfil/views.py
from django.shortcuts import render, redirect
from applications.registro.models import Aprendiz, Instructor, Bienestar
from django.contrib.auth.decorators import login_required


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