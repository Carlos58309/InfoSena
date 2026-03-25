# sesion/views.py
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
from applications.publicaciones.views import get_usuario_actual, usuario_dio_like
from applications.publicaciones.models import Like
import random
from django.utils import timezone
from .models import CodigoRecuperacion
from django.contrib.auth import authenticate, login
from django.db import transaction, connection
from applications.sesion.decorators import sesion_requerida
from django.http import JsonResponse

def login_view(request):
    if request.method == "POST":
        documento = request.POST.get("documento")
        password = request.POST.get("password")

        if not documento or not password:
            messages.warning(request, "Por favor ingresa tu documento y contraseña.")
            return render(request, "login.html")
        
        # ========================================
        # Buscar en Aprendiz
        # ========================================
        aprendiz = Aprendiz.objects.filter(numero_documento=documento).first()
        if aprendiz and aprendiz.contrasena == password:
            
            # ✅ VERIFICAR SI EL CORREO ESTÁ VERIFICADO
            if not aprendiz.verificado:
                messages.error(request, '⚠️ Debes verificar tu correo electrónico antes de iniciar sesión.')
                return render(request, "login.html")
            
            # Login exitoso
            Sesion.objects.create(numero_documento=documento, rol="Aprendiz", exito=True)
            messages.success(request, f"Bienvenido {aprendiz.nombre} (Aprendiz)")
            request.session["rol"] = "Aprendiz"
            request.session["nombre"] = aprendiz.nombre
            request.session["usuario_id"] = documento
            request.session["tipo_usuario"] = "aprendiz"
            return redirect("sesion:home")

        # ========================================
        # Buscar en Instructor
        # ========================================
        instructor = Instructor.objects.filter(numero_documento=documento).first()
        if instructor and instructor.contrasena == password:
            
            # ✅ VERIFICAR SI EL CORREO ESTÁ VERIFICADO
            if not instructor.verificado:
                messages.error(request, '⚠️ Debes verificar tu correo electrónico antes de iniciar sesión.')
                return render(request, "login.html")
            
            # ✅ VERIFICAR SI ESTÁ APROBADO POR ADMIN
            if not instructor.verificado_admin:
                messages.warning(request, '⏳ Tu cuenta está pendiente de aprobación administrativa. Te notificaremos cuando sea aprobada.')
                return render(request, "login.html")
            
            # Login exitoso
            Sesion.objects.create(numero_documento=documento, rol="Instructor", exito=True)
            messages.success(request, f"Bienvenido {instructor.nombre} (Instructor)")
            request.session["rol"] = "Instructor"
            request.session["nombre"] = instructor.nombre
            request.session["usuario_id"] = documento
            request.session["tipo_usuario"] = "instructor"
            return redirect("sesion:home")

        # ========================================
        # Buscar en Bienestar
        # ========================================
        bienestar = Bienestar.objects.filter(numero_documento=documento).first()
        if bienestar and bienestar.contrasena == password:
            
            # ✅ VERIFICAR SI EL CORREO ESTÁ VERIFICADO
            if not bienestar.verificado:
                messages.error(request, '⚠️ Debes verificar tu correo electrónico antes de iniciar sesión.')
                return render(request, "login.html")
            
            # ✅ VERIFICAR SI ESTÁ APROBADO POR ADMIN
            if not bienestar.verificado_admin:
                messages.warning(request, '⏳ Tu cuenta está pendiente de aprobación administrativa. Te notificaremos cuando sea aprobada.')
                return render(request, "login.html")
            
            # Login exitoso
            Sesion.objects.create(numero_documento=documento, rol="Bienestar", exito=True)
            messages.success(request, f"Bienvenido {bienestar.nombre} (Bienestar)")
            request.session["rol"] = "Bienestar"
            request.session["nombre"] = bienestar.nombre
            request.session["usuario_id"] = documento
            request.session["tipo_usuario"] = "bienestar"
            return redirect("sesion:home")

        # ========================================
        # Si no coincide nada
        # ========================================
        Sesion.objects.create(numero_documento=documento, rol="Desconocido", exito=False)
        messages.error(request, "Número de documento o contraseña incorrectos.")
        return render(request, "login.html")

    return render(request, "login.html")


@sesion_requerida
def dashboard_view(request):
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
        return redirect('sesion:login')
    
    publicaciones = Publicacion.objects.filter(activa=True)
    
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
    }
    
    return render(request, "home.html", context)


# ==========================================
# FUNCIÓN HELPER PARA OBTENER USUARIO
# ==========================================
def obtener_usuario_actual(request):
    """
    Obtiene el Usuario de la tabla Usuario basado en la sesión.
    Retorna: (usuario_actual, datos_usuario) o (None, None)
    """
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    print(f"\n🔍 [obtener_usuario_actual] Doc: {usuario_id}, Tipo: {tipo_perfil}")
    
    if not usuario_id or not tipo_perfil:
        print("❌ No hay datos de sesión")
        return None, None
    
    # Buscar el perfil específico
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            print(f"❌ Tipo no reconocido: {tipo_perfil}")
            return None, None
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist) as e:
        print(f"❌ Perfil no encontrado: {e}")
        return None, None
    
    print(f"✅ Perfil: {datos_usuario.nombre} (Doc: {datos_usuario.numero_documento})")
    
    # Buscar Usuario correspondiente
    try:
        usuario_actual = Usuario.objects.get(documento=datos_usuario.numero_documento)
        print(f"✅ Usuario: ID {usuario_actual.id}, Nombre: {usuario_actual.nombre}")
        return usuario_actual, datos_usuario
    except Usuario.DoesNotExist:
        print(f"❌ No existe Usuario con documento: {datos_usuario.numero_documento}")
        return None, datos_usuario
    except Usuario.MultipleObjectsReturned:
        print(f"⚠️  Múltiples Usuarios, tomando el primero")
        usuario_actual = Usuario.objects.filter(documento=datos_usuario.numero_documento).first()
        return usuario_actual, datos_usuario


# ==========================================
# FUNCIÓN DE SUGERENCIAS MEJORADA
# ==========================================
def obtener_sugerencias_inteligentes(usuario_actual, tipo_perfil_actual, limite=10):
    """
    Algoritmo mejorado que SIEMPRE retorna sugerencias si hay usuarios disponibles.
    """
    
    print(f"\n💡 [obtener_sugerencias] Usuario: {usuario_actual.nombre} (ID: {usuario_actual.id})")
    
    # 1. Obtener amigos
    mis_amigos = Amistad.obtener_amigos(usuario_actual)
    ids_mis_amigos = set(amigo.id for amigo in mis_amigos)
    print(f"   👥 Amigos: {len(ids_mis_amigos)}")
    
    # 2. Obtener solicitudes (enviadas Y recibidas)
    ids_solicitudes_enviadas = set(Amistad.objects.filter(
        emisor=usuario_actual, estado=Amistad.PENDIENTE
    ).values_list('receptor_id', flat=True))
    
    ids_solicitudes_recibidas = set(Amistad.objects.filter(
        receptor=usuario_actual, estado=Amistad.PENDIENTE
    ).values_list('emisor_id', flat=True))
    
    # 3. Obtener amistades aceptadas (en ambas direcciones)
    ids_amistades_emisor = set(Amistad.objects.filter(
        emisor=usuario_actual, estado=Amistad.ACEPTADA
    ).values_list('receptor_id', flat=True))
    
    ids_amistades_receptor = set(Amistad.objects.filter(
        receptor=usuario_actual, estado=Amistad.ACEPTADA
    ).values_list('emisor_id', flat=True))
    
    print(f"   📤 Solicitudes enviadas: {len(ids_solicitudes_enviadas)}")
    print(f"   📥 Solicitudes recibidas: {len(ids_solicitudes_recibidas)}")
    print(f"   ✅ Amistades (emisor): {len(ids_amistades_emisor)}")
    print(f"   ✅ Amistades (receptor): {len(ids_amistades_receptor)}")
    
    # 4. Combinar TODOS los IDs a excluir
    ids_excluidos = (
        {usuario_actual.id} | 
        ids_solicitudes_enviadas | 
        ids_solicitudes_recibidas | 
        ids_amistades_emisor | 
        ids_amistades_receptor
    )
    
    print(f"   🚫 Total IDs excluidos: {len(ids_excluidos)} - {ids_excluidos}")
    
    # 5. Obtener candidatos
    candidatos = Usuario.objects.exclude(id__in=ids_excluidos)
    print(f"   🎯 Candidatos encontrados: {candidatos.count()}")
    
    if candidatos.count() == 0:
        print("   ⚠️  No hay candidatos disponibles")
        return []
    
    # Listar candidatos
    for c in candidatos:
        print(f"      - ID: {c.id} | {c.nombre} | {c.tipo}")
    
    # 6. Calcular scores
    sugerencias_con_score = []
    
    for candidato in candidatos:
        score = 5  # Base score para que todos aparezcan
        
        # Amigos en común (solo si tengo amigos)
        amigos_comunes_ids = set()
        cantidad_amigos_comun = 0
        
        if len(ids_mis_amigos) > 0:
            amigos_candidato = Amistad.obtener_amigos(candidato)
            ids_amigos_candidato = set(amigo.id for amigo in amigos_candidato)
            amigos_comunes_ids = ids_mis_amigos & ids_amigos_candidato
            cantidad_amigos_comun = len(amigos_comunes_ids)
            score += cantidad_amigos_comun * 100
        
        # Mismo tipo (+50 puntos)
        mismo_tipo = candidato.tipo == tipo_perfil_actual
        if mismo_tipo:
            score += 50
        
        # Tiene foto (+10 puntos)
        if candidato.foto:
            score += 10
        
        # Lista de amigos en común (max 3)
        amigos_comunes_lista = []
        if amigos_comunes_ids:
            amigos_comunes_lista = list(Usuario.objects.filter(
                id__in=list(amigos_comunes_ids)[:3]
            ))
        
        sugerencias_con_score.append({
            'usuario': candidato,
            'amigos_en_comun': cantidad_amigos_comun,
            'amigos_en_comun_lista': amigos_comunes_lista,
            'prioridad': score,
            'mismo_tipo': mismo_tipo
        })
    
    # 7. Ordenar por prioridad
    sugerencias_ordenadas = sorted(
        sugerencias_con_score,
        key=lambda x: (-x['prioridad'], x['usuario'].nombre)
    )
    
    # Debug
    print(f"   📊 Sugerencias ordenadas:")
    for i, sug in enumerate(sugerencias_ordenadas[:5], 1):
        print(f"      {i}. {sug['usuario'].nombre} - "
              f"Score: {sug['prioridad']} - "
              f"Amigos común: {sug['amigos_en_comun']}")
    
    resultado = sugerencias_ordenadas[:limite]
    print(f"   ✅ Retornando {len(resultado)} sugerencias\n")
    
    return resultado


# ==========================================
# ⭐ VISTA HOME CORREGIDA
# ==========================================
@sesion_requerida
def home_view(request):
    print("\n" + "=" * 100)
    print("🏠 HOME VIEW")
    print("=" * 100)

    usuario_actual, datos_usuario = obtener_usuario_actual(request)

    if not datos_usuario:
        print("❌ No se encontró datos_usuario")
        return redirect('sesion:login')

    tipo_perfil = request.session.get('tipo_usuario')
    print(f"📋 Tipo perfil: {tipo_perfil}")

    # ✅ Obtener usuario y ct para likes
    usuario_like, ct_like = get_usuario_actual(request.session)

    publicaciones = Publicacion.objects.filter(activa=True).prefetch_related(
        'archivos', 'comentarios', 'likes'
    ).order_by('-fecha_creacion')
    print(f"📰 Publicaciones: {publicaciones.count()}")

    # ✅ Anotar likes CORRECTAMENTE
    for pub in publicaciones:
        pub.yo_di_like = usuario_dio_like(pub, usuario_like, ct_like)

    solicitudes_recibidas = []
    sugerencias = []
    amigos = []

    if usuario_actual:
        print(f"✅ usuario_actual: {usuario_actual.nombre}")

        try:
            solicitudes_queryset = Amistad.objects.filter(
                receptor=usuario_actual,
                estado=Amistad.PENDIENTE
            ).select_related('emisor').order_by('-fecha_solicitud')[:5]
            solicitudes_recibidas = list(solicitudes_queryset)
            print(f"📬 Solicitudes: {len(solicitudes_recibidas)}")
        except Exception as e:
            print(f"❌ Error solicitudes: {e}")
            solicitudes_recibidas = []

        try:
            amigos = list(Amistad.obtener_amigos(usuario_actual))
            print(f"👥 Amigos: {len(amigos)}")
        except Exception as e:
            print(f"❌ Error amigos: {e}")
            amigos = []

        try:
            sugerencias = obtener_sugerencias_inteligentes(usuario_actual, tipo_perfil, limite=10)
            print(f"💡 Sugerencias: {len(sugerencias)}")
        except Exception as e:
            print(f"❌ Error sugerencias: {e}")
            sugerencias = []
    else:
        print("⚠️ usuario_actual es None")

    usuario_unificado = Usuario.objects.get(documento=request.session['usuario_id'])

    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
        'solicitudes_recibidas': solicitudes_recibidas,
        'sugerencias': sugerencias,
        'amigos': amigos,
        'es_admin': usuario_unificado.es_admin,
    }

    print("=" * 100 + "\n")
    return render(request, 'home.html', context)


# ==========================================
# VISTA AMIGOS
# ==========================================
@sesion_requerida
def amigos_view(request):
    """Vista de amigos con sugerencias"""
    
    print("\n" + "=" * 100)
    print("👥 VISTA AMIGOS")
    print("=" * 100)
    
    usuario_actual, datos_usuario = obtener_usuario_actual(request)
    
    if not datos_usuario:
        messages.error(request, 'No se pudo cargar tu perfil.')
        return redirect('sesion:login')
    
    if not usuario_actual:
        messages.error(request, 'Tu perfil no está sincronizado.')
        return redirect('sesion:home')
    
    tipo_perfil = request.session.get('tipo_usuario')
    
    # Solicitudes recibidas
    solicitudes_recibidas = Amistad.objects.filter(
        receptor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('emisor').order_by('-fecha_solicitud')
    
    # Solicitudes enviadas
    solicitudes_enviadas = Amistad.objects.filter(
        emisor=usuario_actual,
        estado=Amistad.PENDIENTE
    ).select_related('receptor')
    ids_con_solicitud = set(sol.receptor.id for sol in solicitudes_enviadas)
    
    # Amigos
    amigos = Amistad.obtener_amigos(usuario_actual)
    
    # Sugerencias
    sugerencias = obtener_sugerencias_inteligentes(usuario_actual, tipo_perfil, limite=20)
    usuario = Usuario.objects.get(documento=request.session['usuario_id'])
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'solicitudes_recibidas': solicitudes_recibidas,
        'solicitudes_enviadas_ids': ids_con_solicitud,
        'sugerencias': sugerencias,
        'amigos': amigos,
        'es_admin': usuario.es_admin,
    }
    
    print("=" * 100 + "\n")
    
    return render(request, 'amigos.html', context)


def perfil_view(request):
    return render(request, "perfil.html")

def chat_view(request):
    return render(request, "chat.html")

def solicitar_correo(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            usuario = Usuario.objects.get(email=email)

            # Eliminar códigos anteriores
            CodigoRecuperacion.objects.filter(usuario=usuario).delete()

            # Generar código
            codigo = str(random.randint(100000, 999999))

            # Guardar código
            CodigoRecuperacion.objects.create(
                usuario=usuario,
                codigo=codigo
            )

            # ✅ Enviar con Resend en lugar de send_mail
            import resend
            resend.api_key = settings.RESEND_API_KEY

            resend.Emails.send({
                "from": f"InfoSENA <{settings.DEFAULT_FROM_EMAIL}>",
                "to": [email],
                "subject": "🔐 Código de Recuperación - INFOSENA",
                "text": f"""
Hola,

Recibimos una solicitud para restablecer tu contraseña en INFOSENA.

Tu código de verificación es: {codigo}

Si no solicitaste este cambio, ignora este correo.

Saludos,
Equipo INFOSENA
                """,
            })

            request.session["usuario_recuperacion"] = usuario.id
            return redirect("sesion:verificar_codigo")

        except Usuario.DoesNotExist:
            messages.error(request, "El correo no está registrado.")
        except Exception as e:
            print(f"Error al enviar correo de recuperación: {e}")
            messages.error(request, "Error al enviar el correo. Intenta nuevamente.")

    return render(request, "solicitar_correo.html")


def logout_view(request):
    """Cierra la sesión completamente y previene acceso con botón atrás"""
    # Limpiar completamente la sesión del servidor
    request.session.flush()  # Elimina la sesión y crea una nueva vacía
    
    response = redirect('sesion:login')
    
    # Forzar al navegador a NO guardar en caché esta respuesta
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

def verificar_sesion(request):
    """
    Endpoint que el frontend consulta para saber si la sesión sigue activa.
    Usado por el script anti-caché del botón atrás.
    """
    autenticado = bool(
        request.session.get('usuario_id') and
        request.session.get('tipo_usuario')
    )
    return JsonResponse({'autenticado': autenticado})

def home(request):
    return render(request, 'index.html')

def verificar_codigo(request):

    if request.method == "POST":
        codigo_ingresado = request.POST.get("codigo")
        usuario_id = request.session.get("usuario_recuperacion")

        if not usuario_id:
            return redirect("sesion:login")

        try:
            codigo_obj = CodigoRecuperacion.objects.get(
                usuario_id=usuario_id,
                codigo=codigo_ingresado
            )

            return redirect("sesion:nueva_contrasena")

        except CodigoRecuperacion.DoesNotExist:
            messages.error(request, "Código incorrecto.")

    return render(request, "codigo_restablecer_contraseña.html")

def nueva_contrasena(request):
    usuario_id = request.session.get("usuario_recuperacion")

    if not usuario_id:
        return redirect("sesion:login")

    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("sesion:nueva_contrasena")

        try:
            # Cerrar cualquier conexión existente antes de empezar
            connection.close()
            
            with transaction.atomic():
                usuario = Usuario.objects.select_for_update().get(id=usuario_id)

                # Actualizar auth_user
                if hasattr(usuario, 'user') and usuario.user:
                    usuario.user.set_password(password1)
                    usuario.user.save(update_fields=['password'])

                # Actualizar la tabla correspondiente
                if usuario.tipo == "aprendiz":
                    Aprendiz.objects.filter(numero_documento=usuario.numero_documento).update(
                        contrasena=password1
                    )

                elif usuario.tipo == "instructor":
                    Instructor.objects.filter(numero_documento=usuario.numero_documento).update(
                        contrasena=password1
                    )

                elif usuario.tipo == "bienestar":
                    Bienestar.objects.filter(numero_documento=usuario.numero_documento).update(
                        contrasena=password1
                    )

                # Eliminar códigos de recuperación
                CodigoRecuperacion.objects.filter(usuario=usuario).delete()

            # Limpiar sesión
            request.session.pop("usuario_recuperacion", None)
            request.session.modified = True

            messages.success(request, "Contraseña actualizada correctamente.")
            
            # Cerrar conexión antes de redirigir
            connection.close()
            
            return redirect("sesion:login")

        except Usuario.DoesNotExist:
            connection.close()
            messages.error(request, "Usuario no encontrado.")
            return redirect("sesion:login")
            
        except Exception as e:
            connection.close()
            messages.error(request, f"Error al actualizar la contraseña.")
            print(f"Error detallado: {e}")  # Para debug
            return redirect("sesion:nueva_contrasena")

    return render(request, "restablecer_password.html")