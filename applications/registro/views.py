from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from .models import Aprendiz, Bienestar, Instructor


def registro_view(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        rol = request.POST.get('rol', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()
        region = request.POST.get('region', '').strip()
        contrasena = request.POST.get('password', '').strip()
        tipo_documento = request.POST.get('tipo_documento', '').strip()
        centro_formativo = request.POST.get('centro_formativo', '').strip()

        # Validaciones básicas
        if not all([rol, nombre, email, numero_documento, region, contrasena, tipo_documento]):
            messages.error(request, '⚠️ Todos los campos son obligatorios.')
            return render(request, 'registrar.html')

        # Validar número de documento
        if not numero_documento.isdigit():
            messages.error(request, '❌ El número de documento solo puede contener números.')
            return render(request, 'registrar.html')

        if not (8 <= len(numero_documento) <= 12):
            messages.error(request, '❌ El número de documento debe tener entre 8 y 12 dígitos.')
            return render(request, 'registrar.html')

        # Validar contraseña
        if not (8 <= len(contrasena) <= 12):
            messages.error(request, '❌ La contraseña debe tener entre 8 y 12 caracteres.')
            return render(request, 'registrar.html')

       

        try:
            # Crear registro según el rol
            if rol == 'aprendiz':
                jornada = request.POST.get('jornada', '').strip()
                ficha = request.POST.get('ficha', '').strip()
                
                if not all([jornada, ficha, centro_formativo]):
                    messages.error(request, '⚠️ Complete todos los campos de aprendiz.')
                    return render(request, 'registrar.html')
                
                Aprendiz.objects.create(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    jornada=jornada,
                    ficha=ficha,
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Aprendiz registrado correctamente.')

            elif rol == 'bienestar':
                if not centro_formativo:
                    centro_formativo = "Centro desconocido"
                
                Bienestar.objects.create(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Bienestar registrado correctamente.')

            elif rol == 'instructor':
                if not centro_formativo:
                    messages.error(request, '⚠️ El centro formativo es obligatorio para instructores.')
                    return render(request, 'registrar.html')
                
                Instructor.objects.create(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Instructor registrado correctamente.')

            else:
                messages.error(request, '❌ Rol no válido.')
                return render(request, 'registrar.html')

            # Redirigir al home después del registro exitoso
            return redirect('sesion:home')  # Ajusta según tu configuración de URLs

        except IntegrityError as e:
            if 'numero_documento' in str(e):
                messages.error(request, '❌ El número de documento ya está registrado.')
            elif 'email' in str(e):
                messages.error(request, '❌ El email ya está registrado.')
            else:
                messages.error(request, '❌ Error: Este registro ya existe.')
            return render(request, 'registrar.html')
        
        except Exception as e:
            messages.error(request, f'⚠️ Error inesperado al registrar: {str(e)}')
            return render(request, 'registrar.html')

    # GET request
    return render(request, 'registrar.html')

def amigos_view(request):

    # Obtener todos los usuarios de las 3 tablas
    aprendices = Aprendiz.objects.all()
    instructores = Instructor.objects.all()
    bienestar = Bienestar.objects.all()

    # Unificarlos en una sola lista
    usuarios = []

    for a in aprendices:
        usuarios.append({
            "nombre": a.nombre,
            "email": a.email,
            "modelo": "Aprendiz",
        })

    for i in instructores:
        usuarios.append({
            "nombre": i.nombre,
            "email": i.email,
            "modelo": "Instructor",
        })

    for b in bienestar:
        usuarios.append({
            "nombre": b.nombre,
            "email": b.email,
            "modelo": "Bienestar al Aprendiz",
        })

    return render(request, "amigos.html", {"usuarios": usuarios})
from django.shortcuts import render
