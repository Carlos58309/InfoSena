from django.shortcuts import render, redirect
from django.contrib import messages
from .utils import token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from applications.registro.models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
from applications.amistades.models import Amistad
from .models import Sesion
from django.contrib.auth.decorators import login_required
from applications.publicaciones.models import Publicacion

def login_view(request):
    if request.method == "POST":
        documento = request.POST.get("documento")
        password = request.POST.get("password")

        # Evita errores si no se ingresan datos
        if not documento or not password:
            messages.warning(request, "Por favor ingresa tu documento y contraseña.")
            return render(request, "login.html")
        
        # Buscar en Aprendiz
        aprendiz = Aprendiz.objects.filter(numero_documento=documento).first()
        if aprendiz and aprendiz.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Aprendiz", exito=True)
            messages.success(request, f"Bienvenido {aprendiz.nombre} (Aprendiz)")
            request.session["rol"] = "Aprendiz"
            request.session["nombre"] = aprendiz.nombre
            request.session["usuario_id"] = documento   # guarda el documento como ID
            request.session["tipo_usuario"] = "aprendiz"  # o "instructor", "bienestar" según caso
            return redirect("sesion:home")

        # Buscar en Instructor
        instructor = Instructor.objects.filter(numero_documento=documento).first()
        if instructor and instructor.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Instructor", exito=True)
            messages.success(request, f"Bienvenido {instructor.nombre} (Instructor)")
            request.session["rol"] = "Instructor"
            request.session["nombre"] = instructor.nombre
            request.session["usuario_id"] = documento   # guarda el documento como ID
            request.session["tipo_usuario"] = "instructor"  # o "instructor", "bienestar" según caso
            return redirect("sesion:home")

        # Buscar en Bienestar
        bienestar = Bienestar.objects.filter(numero_documento=documento).first()
        if bienestar and bienestar.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Bienestar", exito=True)
            messages.success(request, f"Bienvenido {bienestar.nombre} (Bienestar)")
            request.session["rol"] = "Bienestar"
            request.session["nombre"] = bienestar.nombre
            request.session["usuario_id"] = documento   # guarda el documento como ID
            request.session["tipo_usuario"] = "bienestar"  # o "instructor", "bienestar" según caso
            return redirect("sesion:home")

        # Si no coincide nada
        Sesion.objects.create(numero_documento=documento, rol="Desconocido", exito=False)
        messages.error(request, "Número de documento o contraseña incorrectos.")
        return render(request, "login.html")

    # Si es un GET (solo mostrar el formulario)
    return render(request, "login.html")


@login_required
def dashboard_view(request):
    """
    Vista para mostrar el home/dashboard del usuario
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
        return redirect('sesion:login')
    
# Traer todas las publicaciones activas (ordenadas por fecha de creación)
    publicaciones = Publicacion.objects.filter(activa=True)
    
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
    }
    
    return render(request, "home.html", context)


@login_required
def amigos_view(request):
    # Obtener datos de la sesión
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    # Obtener el perfil según el tipo
    datos_usuario = None
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        messages.error(request, 'Perfil no encontrado.')
        return redirect('sesion:login')
    
    # ⭐ SOLUCIÓN: Buscar el Usuario que coincida con el perfil actual
    # Opción 1: Por nombre (si los nombres coinciden)
    try:
        usuario_actual = Usuario.objects.get(nombre=datos_usuario.nombre)
    except Usuario.DoesNotExist:
        messages.error(request, f'No se encontró el usuario {datos_usuario.nombre} en el sistema de amistades.')
        return redirect('sesion:home')
    except Usuario.MultipleObjectsReturned:
        # Si hay múltiples, usar el email también
        usuario_actual = Usuario.objects.get(
            nombre=datos_usuario.nombre,
            email=datos_usuario.email
        )
    
    print(f"✅ Usuario correcto encontrado: ID {usuario_actual.id}, Nombre: {usuario_actual.nombre}")
    
    # Solicitudes recibidas
    solicitudes_recibidas = Amistad.objects.filter(
        receptor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('emisor')
    
    # Solicitudes enviadas
    solicitudes_enviadas = Amistad.objects.filter(
        emisor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('receptor')
    
    ids_con_solicitud = {sol.receptor.id for sol in solicitudes_enviadas}
    
    # Amigos
    amigos = Amistad.obtener_amigos(usuario_actual)
    ids_amigos = {amigo.id for amigo in amigos}
    
    # IDs de solicitudes recibidas
    ids_solicitudes_recibidas = {sol.emisor.id for sol in solicitudes_recibidas}
    
    # Sugerencias - Excluir correctamente el usuario actual
    sugerencias = Usuario.objects.exclude(
        id=usuario_actual.id
    ).exclude(
        id__in=ids_amigos
    ).exclude(
        id__in=ids_con_solicitud
    ).exclude(
        id__in=ids_solicitudes_recibidas
    )
    
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'solicitudes_recibidas': solicitudes_recibidas,
        'solicitudes_enviadas_ids': ids_con_solicitud,
        'sugerencias': sugerencias,
        'amigos': amigos,
    }
    
    return render(request, 'amigos.html', context)

@login_required
def obtener_usuario_actual(request):
    """Función helper para obtener el Usuario correcto basado en la sesión"""
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            return None, None
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        return None, None
    
    # ⭐ CORRECCIÓN: Buscar por documento en lugar de nombre
    try:
        usuario_actual = Usuario.objects.get(documento=datos_usuario.numero_documento)
        print(f"✅ Usuario encontrado: ID {usuario_actual.id}, Nombre: {usuario_actual.nombre}")
        return usuario_actual, datos_usuario
    except Usuario.DoesNotExist:
        print(f"❌ No se encontró Usuario para documento: {datos_usuario.numero_documento}")
        return None, datos_usuario
    except Usuario.MultipleObjectsReturned:
        # Si hay múltiples, tomar el primero
        usuario_actual = Usuario.objects.filter(
            documento=datos_usuario.numero_documento
        ).first()
        return usuario_actual, datos_usuario
    
    # Buscar el Usuario que coincida con el perfil
    try:
        usuario_actual = Usuario.objects.get(nombre=datos_usuario.nombre)
        return usuario_actual, datos_usuario
    except Usuario.DoesNotExist:
        return None, datos_usuario
    except Usuario.MultipleObjectsReturned:
        usuario_actual = Usuario.objects.get(
            nombre=datos_usuario.nombre,
            email=datos_usuario.email
        )
        return usuario_actual, datos_usuario


@login_required
def home_view(request):
    """Vista principal del home con publicaciones y datos de amistades"""
    
    # Obtener datos de la sesión
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    if not usuario_id or not tipo_perfil:
        return redirect('sesion:login')
    
    # Obtener el usuario actual y su perfil
    usuario_actual, datos_usuario = obtener_usuario_actual(request)
    
    if not datos_usuario:
        return redirect('sesion:login')
    
    # Obtener todas las publicaciones (ordenadas por fecha)
    publicaciones = Publicacion.objects.all().order_by('-fecha_creacion')
    
    # ⭐ DATOS DE AMISTADES (solo si existe usuario_actual)
    solicitudes_recibidas = []
    sugerencias = []
    amigos = []
    
    if usuario_actual:
        # Solicitudes recibidas pendientes
        solicitudes_recibidas = Amistad.objects.filter(
            receptor=usuario_actual,
            estado=Amistad.PENDIENTE
        ).select_related('emisor')[:5]  # Máximo 5 solicitudes
        
        # Amigos aceptados
        amigos = Amistad.obtener_amigos(usuario_actual)
        ids_amigos = {amigo.id for amigo in amigos}
        
        # Solicitudes enviadas
        solicitudes_enviadas = Amistad.objects.filter(
            emisor=usuario_actual,
            estado=Amistad.PENDIENTE
        ).select_related('receptor')
        ids_con_solicitud = {sol.receptor.id for sol in solicitudes_enviadas}
        
        # IDs de solicitudes recibidas
        ids_solicitudes_recibidas = {sol.emisor.id for sol in solicitudes_recibidas}
        
        # Sugerencias (usuarios que no son amigos ni tienen solicitudes pendientes)
        sugerencias = Usuario.objects.exclude(
            id=usuario_actual.id
        ).exclude(
            id__in=ids_amigos
        ).exclude(
            id__in=ids_con_solicitud
        ).exclude(
            id__in=ids_solicitudes_recibidas
        )[:5]  # Máximo 5 sugerencias
    
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
        'solicitudes_recibidas': solicitudes_recibidas,
        'sugerencias': sugerencias,
        'amigos': amigos,
    }
    
    return render(request, 'home.html', context) 

def perfil_view(request):
    return render(request, "perfil.html")

def chat_view(request):
    return render(request, "chat.html")

def solicitar_correo(request):
    if request.method == "POST":
        email = request.POST.get("email")

        usuario = (
            Aprendiz.objects.filter(email=email).first() or
            Instructor.objects.filter(email=email).first() or
            Bienestar.objects.filter(email=email).first()
        )

        if not usuario:
            messages.error(request, "No existe una cuenta asociada a ese correo.")
            return render(request, "solicitar_correo.html")

        token = token_generator.make_token(usuario)
        uid = usuario.pk

        reset_url = request.build_absolute_uri(
            reverse("sesion:restablecer", args=[uid, token])
        )

        send_mail(
            "Restablecer contraseña",
            f"Hola, usa este enlace para restablecer tu contraseña:\n\n{reset_url}",
            "infosenasystem@gmail.com",
            [email],
        )

        messages.success(request, "Se ha enviado un enlace de recuperación a tu correo.")
        return redirect("sesion:login")

    return render(request, "solicitar_correo.html")



# ------------------------------------------
#   VALIDAR TOKEN Y MOSTRAR FORMULARIO
# ------------------------------------------

def restablecer_contrasena(request, uid, token):
    usuario = (
        Aprendiz.objects.filter(pk=uid).first() or
        Instructor.objects.filter(pk=uid).first() or
        Bienestar.objects.filter(pk=uid).first()
    )

    if not usuario or not token_generator.check_token(usuario, token):
        messages.error(request, "El enlace no es válido o ha expirado.")
        return redirect("sesion:solicitar_correo")

    if request.method == "POST":
        nueva = request.POST.get("password1")
        confirmar = request.POST.get("password2")

        if nueva != confirmar:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "restablecer_password.html")

        usuario.contrasena = nueva
        usuario.save()

        messages.success(request, "Tu contraseña ha sido restablecida con éxito.")
        return redirect("sesion:login")  # ✔ te lleva al login correctamente

    return render(request, "restablecer_password.html")

def home(request):
    return render(request, 'index.html')