# registro/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from .models import Aprendiz, Bienestar, Instructor
import re
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from applications.sesion.decorators import sesion_requerida

# ========================================
# FUNCIONES AUXILIARES
# ========================================

def generar_codigo():
    """Genera un código aleatorio de 6 dígitos"""
    return str(random.randint(100000, 999999))


def enviar_codigo_verificacion(email, nombre, codigo):
    """Envía el código de verificación por correo al usuario usando Resend"""
    import resend
    from django.conf import settings

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send({
            "from": f"InfoSENA <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [email],
            "subject": "🔐 Código de Verificación - INFOSENA",
            "text": f"""
Hola {nombre},

¡Bienvenido a INFOSENA! 🎓

Tu código de verificación es: {codigo}

Este código expira en 15 minutos.

Si no solicitaste este registro, ignora este correo.

Saludos,
Equipo INFOSENA
            """,
        })
        return True
    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False


def enviar_notificacion_admin(nombre, email, rol, tipo_doc, num_doc, codigo_admin):
    """Envía notificación al admin para aprobar instructor/bienestar usando Resend"""
    import resend
    from django.conf import settings

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send({
            "from": f"InfoSENA <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [settings.ADMIN_EMAIL],
            "subject": f"⚠️ Nueva Solicitud de Registro - {rol.upper()}",
            "text": f"""
NUEVA SOLICITUD DE REGISTRO COMO {rol.upper()}

Datos del solicitante:
-----------------------------
Nombre: {nombre}
Tipo de documento: {tipo_doc}
Número de documento: {num_doc}
Correo: {email}
Rol solicitado: {rol.upper()}

CÓDIGO DE APROBACIÓN: {codigo_admin}

⚠️ IMPORTANTE: Este usuario necesita aprobación administrativa.
El usuario ya verificó su correo electrónico, pero necesita que ingreses
el código de aprobación para activar su cuenta.

Este código expira en 24 horas.

---
Sistema INFOSENA
            """,
        })
        return True
    except Exception as e:
        print(f"Error al enviar notificación admin: {str(e)}")
        return False


# ========================================
# VISTA: REGISTRO
# ========================================

def registro_view(request):
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
        # VALIDAR DOCUMENTO ÚNICO EN TODAS LAS TABLAS
        # ========================================
        if Aprendiz.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Aprendiz.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        if Instructor.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Instructor.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        if Bienestar.objects.filter(numero_documento=numero_documento).exists():
            messages.error(request, f'❌ El número de documento {numero_documento} ya está registrado como Bienestar.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR EMAIL - SOLO MICROSOFT Y SENA
        # ========================================
        DOMINIOS_PERMITIDOS = [
            # SENA
            'soy.sena.edu.co', 'sena.edu.co'
        ]
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            messages.error(request, '❌ Por favor ingresa un correo electrónico válido.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        # Validar dominio permitido
        email_domain = email.split('@')[-1].lower()
        if email_domain not in DOMINIOS_PERMITIDOS:
            messages.error(request, '❌ Solo se permiten correos del SENA (@sena.edu.co, @soy.sena.edu.co).')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR EMAIL ÚNICO EN TODAS LAS TABLAS
        # ========================================
        if Aprendiz.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Aprendiz.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        if Instructor.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Instructor.')
            return render(request, 'registrar.html', {'form_data': form_data})
        
        if Bienestar.objects.filter(email=email).exists():
            messages.error(request, f'❌ El correo electrónico {email} ya está registrado como Bienestar.')
            return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # VALIDAR CONTRASEÑA COMPLEJA
        # ========================================
        if not (8 <= len(contrasena) <= 12):
            messages.error(request, '❌ La contraseña debe tener entre 8 y 12 caracteres.')
            return render(request, 'registrar.html', {'form_data': form_data})

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
            
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, '❌ La imagen no puede superar los 5MB.')
                return render(request, 'registrar.html', {'form_data': form_data})

        # ========================================
        # GENERAR CÓDIGOS
        # ========================================
        codigo_usuario = generar_codigo()
        expiracion = timezone.now() + timedelta(minutes=15)
        
        # Código admin solo para instructor y bienestar
        codigo_admin = generar_codigo() if rol in ['instructor', 'bienestar'] else None

        # ========================================
        # ENVIAR CÓDIGO AL USUARIO
        # ========================================
        if not enviar_codigo_verificacion(email, nombre, codigo_usuario):
            messages.error(request, '⚠️ Error al enviar el código de verificación. Verifica tu correo.')
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
                
                aprendiz = Aprendiz(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    jornada=jornada,
                    ficha=ficha,
                    region=region,
                    foto=foto if foto else None,
                    verificado=False,
                    codigo_verificacion=codigo_usuario,
                    codigo_expiracion=expiracion
                )
                aprendiz.set_password(contrasena)  # ✅ Encripta aquí
                aprendiz.save()
                request.session['usuario_id'] = aprendiz.numero_documento
                request.session['usuario_tipo'] = 'aprendiz'
                
                messages.success(request, f'📧 Se ha enviado un código de verificación a {email}')
                return redirect('registro:verificar_codigo')

            elif rol == 'bienestar':
                if not centro_formativo:
                    centro_formativo = "Centro Agroempresarial y Desarrollo Pecuario del Huila"
                
                bienestar = Bienestar(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    foto=foto if foto else None,
                    verificado=False,
                    codigo_verificacion=codigo_usuario,
                    codigo_expiracion=expiracion,
                    verificado_admin=False,
                    codigo_admin=codigo_admin
                )
                bienestar.set_password(contrasena)  # ✅ Encripta aquí
                bienestar.save()
                # ENVIAR NOTIFICACIÓN AL ADMIN
                enviar_notificacion_admin(nombre, email, 'Bienestar', tipo_documento, numero_documento, codigo_admin)
                
                request.session['usuario_id'] = bienestar.numero_documento
                request.session['usuario_tipo'] = 'bienestar'
                
                messages.success(request, f'📧 Se ha enviado un código de verificación a {email}')
                messages.info(request, '⚠️ Como Bienestar, tu cuenta requiere aprobación administrativa adicional.')
                return redirect('registro:verificar_codigo')

            elif rol == 'instructor':
                if not centro_formativo:
                    messages.error(request, '⚠️ El centro formativo es obligatorio para instructores.')
                    return render(request, 'registrar.html', {'form_data': form_data})
                
                instructor = Instructor(
                    nombre=nombre,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=centro_formativo,
                    region=region,
                    foto=foto if foto else None,
                    verificado=False,
                    codigo_verificacion=codigo_usuario,
                    codigo_expiracion=expiracion,
                    verificado_admin=False,
                    codigo_admin=codigo_admin
                )
                instructor.set_password(contrasena)  # ✅ Encripta aquí
                instructor.save()
                # ENVIAR NOTIFICACIÓN AL ADMIN
                enviar_notificacion_admin(nombre, email, 'Instructor', tipo_documento, numero_documento, codigo_admin)
                
                request.session['usuario_id'] = instructor.numero_documento
                request.session['usuario_tipo'] = 'instructor'
                
                messages.success(request, f'📧 Se ha enviado un código de verificación a {email}')
                messages.info(request, '⚠️ Como Instructor, tu cuenta requiere aprobación administrativa adicional.')
                return redirect('registro:verificar_codigo')

            else:
                messages.error(request, '❌ Rol no válido.')
                return render(request, 'registrar.html', {'form_data': form_data})

        except IntegrityError as e:
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

    return render(request, 'registrar.html', {'form_data': form_data})


# ========================================
# VISTA: VERIFICAR CÓDIGO
# ========================================

def verificar_codigo_view(request):
    """Vista para verificar el código enviado por email"""
    
    # ✅ VALIDACIÓN DE SESIÓN
    usuario_id = request.session.get('usuario_id')
    usuario_tipo = request.session.get('usuario_tipo')
    
    # DEBUG en consola
    print("=" * 60)
    print("🔍 DEBUG VERIFICACIÓN:")
    print(f"   usuario_id en sesión: {usuario_id}")
    print(f"   usuario_tipo en sesión: {usuario_tipo}")
    print("=" * 60)
    
    if not usuario_id or not usuario_tipo:
        messages.error(request, '❌ Sesión expirada. Regístrate nuevamente.')
        return redirect('registro:registro')
    
    # ✅ BUSCAR USUARIO ANTES DEL POST
    usuario = None
    try:
        if usuario_tipo == 'aprendiz':
            usuario = Aprendiz.objects.filter(numero_documento=usuario_id).first()
        elif usuario_tipo == 'instructor':
            usuario = Instructor.objects.filter(numero_documento=usuario_id).first()
        elif usuario_tipo == 'bienestar':
            usuario = Bienestar.objects.filter(numero_documento=usuario_id).first()
        
        print(f"🔍 Usuario encontrado: {usuario}")
        if usuario:
            print(f"   - Nombre: {usuario.nombre}")
            print(f"   - Email: {usuario.email}")
            print(f"   - Código guardado: {usuario.codigo_verificacion}")
            print(f"   - Verificado: {usuario.verificado}")
            
    except Exception as e:
        print(f"❌ Error al buscar usuario: {str(e)}")
        messages.error(request, f'❌ Error al buscar usuario: {str(e)}')
        return redirect('registro:registro')
    
    if not usuario:
        messages.error(request, '❌ Usuario no encontrado en la base de datos.')
        # Limpiar sesión corrupta
        if 'usuario_id' in request.session:
            del request.session['usuario_id']
        if 'usuario_tipo' in request.session:
            del request.session['usuario_tipo']
        return redirect('registro:registro')
    
    # ✅ VERIFICAR QUE TENGA CÓDIGO PENDIENTE
    if not hasattr(usuario, 'codigo_verificacion') or not usuario.codigo_verificacion:
        messages.error(request, '❌ No hay código de verificación pendiente para este usuario.')
        return redirect('registro:registro')
    
    if not hasattr(usuario, 'codigo_expiracion') or not usuario.codigo_expiracion:
        messages.error(request, '❌ Error en el código de verificación. Por favor regístrate nuevamente.')
        return redirect('registro:registro')
    
    # ========================================
    # PROCESAR FORMULARIO POST
    # ========================================
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()
        
        print(f"🔍 Código ingresado: '{codigo_ingresado}'")
        print(f"🔍 Código esperado: '{usuario.codigo_verificacion}'")
        
        if not codigo_ingresado:
            messages.error(request, '⚠️ Por favor ingresa el código.')
            return render(request, 'verificar_codigo.html')
        
        # Validar formato
        if len(codigo_ingresado) != 6 or not codigo_ingresado.isdigit():
            messages.error(request, '❌ El código debe tener 6 dígitos numéricos.')
            return render(request, 'verificar_codigo.html')
        
        # ✅ VERIFICAR SI EL CÓDIGO YA EXPIRÓ
        if timezone.now() > usuario.codigo_expiracion:
            messages.error(request, '⏰ El código ha expirado. Solicita uno nuevo.')
            return render(request, 'verificar_codigo.html', {'puede_reenviar': True})
        
        # ✅ COMPARAR CÓDIGOS
        if codigo_ingresado == usuario.codigo_verificacion:
            print("✅ Código correcto - Actualizando usuario...")
            
            try:
                # Actualizar usuario
                usuario.verificado = True
                usuario.codigo_verificacion = None
                usuario.codigo_expiracion = None
                usuario.save()
                
                print("✅ Usuario actualizado exitosamente")
                
                # VERIFICAR SI NECESITA APROBACIÓN ADMIN
                if usuario_tipo in ['instructor', 'bienestar']:
                    # Guardar info en sesión para la página de espera
                    request.session['usuario_pendiente'] = usuario_id
                    request.session['tipo_pendiente'] = usuario_tipo
                    
                    # Limpiar sesión de registro
                    if 'usuario_id' in request.session:
                        del request.session['usuario_id']
                    if 'usuario_tipo' in request.session:
                        del request.session['usuario_tipo']
                    
                    messages.success(request, '✅ ¡Correo verificado exitosamente!')
                    return redirect('registro:esperando_aprobacion')
                else:
                    # Aprendiz puede ingresar inmediatamente
                    if 'usuario_id' in request.session:
                        del request.session['usuario_id']
                    if 'usuario_tipo' in request.session:
                        del request.session['usuario_tipo']
                    
                    messages.success(request, '✅ ¡Cuenta verificada exitosamente! Ya puedes iniciar sesión.')
                    return redirect('sesion:login')
                    
            except Exception as e:
                print(f"❌ Error al guardar: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'⚠️ Error al verificar código: {str(e)}')
                return render(request, 'verificar_codigo.html')
        else:
            print("❌ Código incorrecto")
            messages.error(request, '❌ Código incorrecto. Inténtalo de nuevo.')
            return render(request, 'verificar_codigo.html')
    
    # ========================================
    # GET request - mostrar formulario
    # ========================================
    return render(request, 'verificar_codigo.html')


# ========================================
# VISTA: REENVIAR CÓDIGO
# ========================================

def reenviar_codigo_view(request):
    """Reenviar código de verificación"""
    
    if 'usuario_id' not in request.session:
        messages.error(request, '❌ Sesión expirada.')
        return redirect('registro:registro')
    
    usuario_id = request.session.get('usuario_id')
    usuario_tipo = request.session.get('usuario_tipo')
    
    usuario = None
    if usuario_tipo == 'aprendiz':
        usuario = Aprendiz.objects.filter(numero_documento=usuario_id).first()
    elif usuario_tipo == 'instructor':
        usuario = Instructor.objects.filter(numero_documento=usuario_id).first()
    elif usuario_tipo == 'bienestar':
        usuario = Bienestar.objects.filter(numero_documento=usuario_id).first()
    
    if not usuario:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('registro:registro')
    
    nuevo_codigo = generar_codigo()
    nueva_expiracion = timezone.now() + timedelta(minutes=15)
    
    if enviar_codigo_verificacion(usuario.email, usuario.nombre, nuevo_codigo):
        usuario.codigo_verificacion = nuevo_codigo
        usuario.codigo_expiracion = nueva_expiracion
        usuario.save()
        
        messages.success(request, '📧 Se ha enviado un nuevo código a tu correo.')
    else:
        messages.error(request, '⚠️ Error al reenviar el código.')
    
    return redirect('registro:verificar_codigo')


def esperando_aprobacion_view(request):
    """Página de espera para usuarios que necesitan aprobación administrativa"""
    
    if 'usuario_pendiente' not in request.session:
        return redirect('sesion:login')
    
    usuario_id = request.session.get('usuario_pendiente')
    usuario_tipo = request.session.get('tipo_pendiente')
    
    # Buscar usuario
    usuario = None
    if usuario_tipo == 'instructor':
        usuario = Instructor.objects.filter(numero_documento=usuario_id).first()
    elif usuario_tipo == 'bienestar':
        usuario = Bienestar.objects.filter(numero_documento=usuario_id).first()
    
    if not usuario:
        del request.session['usuario_pendiente']
        del request.session['tipo_pendiente']
        return redirect('sesion:login')
    
    # Verificar si ya fue aprobado
    if usuario.verificado_admin:
        messages.success(request, '🎉 ¡Tu cuenta ha sido aprobada! Ya puedes iniciar sesión.')
        del request.session['usuario_pendiente']
        del request.session['tipo_pendiente']
        return redirect('sesion:login')
    
    context = {
        'nombre': usuario.nombre,
        'rol': usuario_tipo.capitalize(),
        'email': usuario.email,
    }
    
    return render(request, 'esperando_aprobacion.html', context)

# ========================================
# VISTA: AMIGOS (sin cambios)
# ========================================
# ========================================
# VISTA: PANEL DE APROBACIÓN ADMIN
# ========================================
@sesion_requerida
def panel_aprobacion_view(request):
    """Panel para que el admin vea y apruebe cuentas pendientes"""
    
    # Obtener todas las cuentas pendientes de aprobación
    instructores_pendientes = Instructor.objects.filter(
        verificado=True,  # Ya verificaron su email
        verificado_admin=False  # Pendientes de aprobación
    )
    
    bienestar_pendientes = Bienestar.objects.filter(
        verificado=True,
        verificado_admin=False
    )
    
    # Combinar en una lista
    pendientes = []
    
    for instructor in instructores_pendientes:
        pendientes.append({
            'tipo': 'Instructor',
            'nombre': instructor.nombre,
            'email': instructor.email,
            'documento': instructor.numero_documento,
            'tipo_documento': instructor.tipo_documento,
            'centro_formativo': instructor.centro_formativo,
            'region': instructor.region,
            'fecha_registro': instructor.numero_documento,  # Puedes agregar un campo fecha si quieres
        })
    
    for bienestar in bienestar_pendientes:
        pendientes.append({
            'tipo': 'Bienestar',
            'nombre': bienestar.nombre,
            'email': bienestar.email,
            'documento': bienestar.numero_documento,
            'tipo_documento': bienestar.tipo_documento,
            'centro_formativo': bienestar.centro_formativo,
            'region': bienestar.region,
            'fecha_registro': bienestar.numero_documento,
        })
    
    context = {
        'pendientes': pendientes,
        'total_pendientes': len(pendientes),
    }
    
    return render(request, 'panel_aprobacion.html', context)


def aprobar_cuenta_view(request):
    """Aprobar una cuenta usando el código administrativo"""
    
    if request.method == 'POST':
        documento = request.POST.get('documento', '').strip()
        codigo_admin = request.POST.get('codigo_admin', '').strip()
        
        if not documento or not codigo_admin:
            messages.error(request, '⚠️ Debes ingresar el documento y el código de aprobación.')
            return redirect('registro:panel_aprobacion')
        
        # Buscar en Instructor
        instructor = Instructor.objects.filter(numero_documento=documento).first()
        if instructor:
            # Verificar código
            if codigo_admin == instructor.codigo_admin:
                instructor.verificado_admin = True
                instructor.codigo_admin = None  # Limpiar código
                instructor.save()
                
                # Enviar email de notificación al usuario
                enviar_notificacion_aprobacion(instructor.email, instructor.nombre, 'Instructor')
                
                messages.success(request, f'✅ Cuenta de {instructor.nombre} aprobada exitosamente.')
                return redirect('registro:panel_aprobacion')
            else:
                messages.error(request, '❌ Código de aprobación incorrecto.')
                return redirect('registro:panel_aprobacion')
        
        # Buscar en Bienestar
        bienestar = Bienestar.objects.filter(numero_documento=documento).first()
        if bienestar:
            # Verificar código
            if codigo_admin == bienestar.codigo_admin:
                bienestar.verificado_admin = True
                bienestar.codigo_admin = None  # Limpiar código
                bienestar.save()
                
                # Enviar email de notificación al usuario
                enviar_notificacion_aprobacion(bienestar.email, bienestar.nombre, 'Bienestar')
                
                messages.success(request, f'✅ Cuenta de {bienestar.nombre} aprobada exitosamente.')
                return redirect('registro:panel_aprobacion')
            else:
                messages.error(request, '❌ Código de aprobación incorrecto.')
                return redirect('registro:panel_aprobacion')
        
        messages.error(request, '❌ No se encontró ninguna cuenta pendiente con ese documento.')
        return redirect('registro:panel_aprobacion')
    
    return redirect('registro:panel_aprobacion')


def enviar_notificacion_aprobacion(email, nombre, rol):
    """Envía email al usuario notificando que su cuenta fue aprobada usando Resend"""
    import resend
    from django.conf import settings

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send({
            "from": f"InfoSENA <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [email],
            "subject": "🎉 Cuenta Aprobada - INFOSENA",
            "text": f"""
Hola {nombre},

¡Excelentes noticias! 🎉

Tu cuenta como {rol} en INFOSENA ha sido APROBADA por el administrador.

Ya puedes iniciar sesión en la plataforma con tu número de documento y contraseña.

¡Bienvenido al equipo INFOSENA!

Saludos,
Equipo INFOSENA
            """,
        })
        return True
    except Exception as e:
        print(f"Error al enviar notificación de aprobación: {str(e)}")
        return False
    
def amigos_view(request):
    aprendices = Aprendiz.objects.all()
    instructores = Instructor.objects.all()
    bienestar = Bienestar.objects.all()

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