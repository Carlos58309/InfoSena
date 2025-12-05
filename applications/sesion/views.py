from django.shortcuts import render, redirect
from django.contrib import messages
from .utils import token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from applications.registro.models import Aprendiz, Instructor, Bienestar
from .models import Sesion

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


def dashboard_view(request):
    # Si el usuario no tiene sesión, redirige al login
    if "rol" not in request.session:
        messages.warning(request, "Debes iniciar sesión para acceder al panel.")
        return redirect("sesion:login")

    contexto = {
        "nombre": request.session.get("nombre"),
        "rol": request.session.get("rol"),
    }
    return render(request, "home.html", contexto)


def amigos_view(request):
    usuarios = []

    # Cargar aprendices
    usuarios += list(Aprendiz.objects.all())

    # Cargar instructores
    usuarios += list(Instructor.objects.all())

    # Cargar bienestar
    usuarios += list(Bienestar.objects.all())

    return render(request, "amigos.html", {
        "usuarios": usuarios
    })

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