from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from .models import Aprendiz, Bienestar, Instructor
import re


def registro_view(request):
    # Guardar los datos del formulario en caso de error
    form_data = {}
    
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
        
        # Guardar datos para repoblar el formulario en caso de error
        form_data = {
            'rol': rol,
            'nombre': nombre,
            'email': email,
            'numero_documento': numero_documento,
            'tipo_documento': tipo_documento,
            'jornada': request.POST.get('jornada', '').strip(),
            'ficha': request.POST.get('ficha', '').strip(),
        }
        
        # Obtener la foto de perfil (si existe)
        foto = request.FILES.get('foto')

        # ========================================
        # VALIDACIONES BÁSICAS
        # ========================================
        if not all([rol, nombre, email, numero_documento, region, contrasena, tipo_documento]):
            messages.error(request, '⚠️ Todos los campos son obligatorios.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR NÚMERO DE DOCUMENTO (SOLO NÚMEROS)
        # ========================================
        if not numero_documento.isdigit():
            messages.error(request, '❌ El número de documento solo puede contener números.')
            return render(request, 'registrar.html', {'form_data': form_data})

        if not (7 <= len(numero_documento) <= 12):
            messages.error(request, '❌ El número de documento debe tener entre 7 y 12 dígitos.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # ⭐ VALIDACIÓN NUEVA: DOCUMENTO ÚNICO EN TODAS LAS TABLAS
        # ========================================
        # Verificar si el documento ya existe en Aprendiz
        if Aprendiz.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Aprendiz. No puedes usar este documento nuevamente.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        # Verificar si el documento ya existe en Instructor
        if Instructor.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Instructor. No puedes usar este documento nuevamente.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        # Verificar si el documento ya existe en Bienestar
        if Bienestar.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Bienestar. No puedes usar este documento nuevamente.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR EMAIL
        # ========================================
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            messages.error(request, '❌ Por favor ingresa un correo electrónico válido.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # ⭐ VALIDACIÓN NUEVA: EMAIL ÚNICO EN TODAS LAS TABLAS
        # ========================================
        # Verificar si el email ya existe en Aprendiz
        if Aprendiz.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Aprendiz. Usa otro correo.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        # Verificar si el email ya existe en Instructor
        if Instructor.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Instructor. Usa otro correo.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        # Verificar si el email ya existe en Bienestar
        if Bienestar.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Bienestar. Usa otro correo.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR CONTRASEÑA COMPLEJA
        # ========================================
        if not (8 <= len(contrasena) <= 12):
            messages.error(request, '❌ La contraseña debe tener entre 8 y 12 caracteres.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # Validar requisitos de contraseña
        tiene_mayuscula = bool(re.search(r'[A-Z]', contrasena))
        tiene_minuscula = bool(re.search(r'[a-z]', contrasena))
        cantidad_numeros = len(re.findall(r'\d', contrasena))
        tiene_especial = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', contrasena))

        errores_contrasena = []
        if not tiene_mayuscula:
            errores_contrasena.append('al menos 1 letra mayúscula')
        if not tiene_minuscula:
            errores_contrasena.append('al menos 1 letra minúscula')
        if cantidad_numeros < 3:
            errores_contrasena.append('al menos 3 números')
        if not tiene_especial:
            errores_contrasena.append('al menos 1 carácter especial (!@#$%^&*)')

        if errores_contrasena:
            mensaje_error = f"❌ La contraseña debe contener: {', '.join(errores_contrasena)}."
            messages.error(request, mensaje_error)
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR FORMATO DE IMAGEN (opcional)
        # ========================================
        if foto:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_extension = foto.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                messages.error(request, '❌ Solo se permiten imágenes (JPG, JPEG, PNG, GIF).')
                return render(request, 'registrar.html', {'form_data': form_data})
            
            # Validar tamaño (máximo 5MB)
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, '❌ La imagen no puede superar los 5MB.')
                return render(request, 'registrar.html', {'form_data': form_data})

        try:
            # ========================================
            # CREAR REGISTRO SEGÚN EL ROL
            # ========================================
            if rol == 'aprendiz':
                jornada = request.POST.get('jornada', '').strip()
                ficha = request.POST.get('ficha', '').strip()
                
                if not all([jornada, ficha, centro_formativo]):
                    messages.error(request, '⚠️ Complete todos los campos de aprendiz.')
                    return render(request, 'registrar.html', {'form_data': form_data})
                
                aprendiz = Aprendiz.objects.create(
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
                
                if foto:
                    aprendiz.foto = foto
                    aprendiz.save()
                
                messages.success(request, f'✅ ¡Bienvenido {nombre}! Tu cuenta de aprendiz ha sido creada exitosamente.')

            elif rol == 'bienestar':
                if not centro_formativo:
                    centro_formativo = "Centro Agroempresarial y Desarrollo Pecuario del Huila"
                
                bienestar = Bienestar.objects.create(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    contrasena=contrasena
                )
                
                if foto:
                    bienestar.foto = foto
                    bienestar.save()
                
                messages.success(request, f'✅ ¡Bienvenido {nombre}! Tu cuenta de bienestar ha sido creada exitosamente.')

            elif rol == 'instructor':
                if not centro_formativo:
                    messages.error(request, '⚠️ El centro formativo es obligatorio para instructores.')
                    return render(request, 'registrar.html', {'form_data': form_data})
                
                instructor = Instructor.objects.create(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    contrasena=contrasena
                )
                
                if foto:
                    instructor.foto = foto
                    instructor.save()
                
                messages.success(request, f'✅ ¡Bienvenido {nombre}! Tu cuenta de instructor ha sido creada exitosamente.')

            else:
                messages.error(request, '❌ Rol no válido.')
                return render(request, 'registrar.html', {'form_data': form_data})

            # Redirigir al login después del registro exitoso
            messages.info(request, '👉 Ahora puedes iniciar sesión con tu número de documento y contraseña.')
            return redirect('sesion:login')

        except IntegrityError as e:
            # Este bloque es backup por si las validaciones manuales fallan
            if 'numero_documento' in str(e):
                messages.error(request, '❌ El número de documento ya está registrado.')
            elif 'email' in str(e):
                messages.error(request, '❌ El email ya está registrado.')
            else:
                messages.error(request, '❌ Error: Este registro ya existe.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        except Exception as e:
            messages.error(request, f'⚠️ Error inesperado al registrar: {str(e)}')
            return render(request, 'registrar.html', {'form_data': form_data})

    # GET request
    return render(request, 'registrar.html', {'form_data': form_data})


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