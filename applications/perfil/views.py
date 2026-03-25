# applications/perfil/views.py - VERSIÓN SIMPLIFICADA

from django.shortcuts import render, redirect, get_object_or_404
from applications.registro.models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
from applications.perfil.models import PrivacidadPerfil
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
import os
from django.conf import settings
from django.core.files.storage import default_storage
from applications.publicaciones.models import Publicacion
from applications.publicaciones.views import get_usuario_actual, usuario_dio_like
from applications.amistades.models import Amistad
from applications.sesion.decorators import sesion_requerida
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from applications.publicaciones.models import Like
# ========================================
# VISTA: PERFIL PROPIO
# ========================================
@sesion_requerida
def perfiles(request):
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')

    usuario_id = request.session['usuario_id']
    tipo_perfil = request.session['tipo_usuario']
    datos_usuario = None
    publicaciones = None

    print(f"\n{'='*60}")
    print(f"🏠 PERFILES - Perfil propio")
    print(f"{'='*60}")
    print(f"Usuario ID: {usuario_id} | Tipo: {tipo_perfil}")

    # ✅ Obtener usuario y ct para likes
    usuario_like, ct_like = get_usuario_actual(request.session)

    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
            print(f"✅ Aprendiz: {datos_usuario.nombre}")

        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
            print(f"✅ Instructor: {datos_usuario.nombre}")

        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
            print(f"✅ Bienestar: {datos_usuario.nombre}")

            try:
                publicaciones = Publicacion.objects.filter(
                    autor__numero_documento=usuario_id,
                    activa=True
                ).prefetch_related('archivos', 'comentarios', 'likes').order_by('-fecha_creacion')

                print(f"✅ Publicaciones encontradas: {publicaciones.count()}")

                # ✅ Anotar likes CORRECTAMENTE
                for pub in publicaciones:
                    pub.yo_di_like = usuario_dio_like(pub, usuario_like, ct_like)

            except Exception as e:
                print(f"❌ Error publicaciones: {e}")
                import traceback
                traceback.print_exc()
                publicaciones = None

    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist) as e:
        print(f"❌ Usuario no encontrado: {e}")
        return redirect('sesion:login')

    print(f"{'='*60}\n")

    usuario_unificado = Usuario.objects.get(documento=usuario_id)
    privacidad_config = PrivacidadPerfil.obtener_o_crear(usuario_id)

    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
        'es_admin': usuario_unificado.es_admin,
        'privacidad': privacidad_config,
    }

    return render(request, 'perfil.html', context)


# Alias para compatibilidad

def perfil(request):
    """Alias de perfiles() para mantener compatibilidad"""
    return perfiles(request)


# ========================================
# VISTA: DASHBOARD
# ========================================
@sesion_requerida
def dashboard_view(request):
    """Dashboard del usuario"""
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
    
    publicaciones = Publicacion.objects.filter(activa=True).order_by('-fecha_creacion')
    usuario = Usuario.objects.get(documento=request.session['usuario_id'])
    context = {
        'usuario': datos_usuario,
        'tipo_perfil': tipo_perfil,
        'publicaciones': publicaciones,
        'es_admin': usuario.es_admin,
    }
    return render(request, "home.html", context)


# ========================================
# VISTA: EDITAR PERFIL
# ========================================
@sesion_requerida
def editar_perfil(request):
    """Editar el perfil del usuario"""
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
    
    if request.method == 'POST':
        datos_usuario.nombre = request.POST.get('nombre')
        datos_usuario.email = request.POST.get('email')
        datos_usuario.tipo_documento = request.POST.get('tipo_documento')
        datos_usuario.centro_formativo = request.POST.get('centro_formativo')
        datos_usuario.region = request.POST.get('region')

        if tipo_perfil == 'aprendiz':
            datos_usuario.ficha = request.POST.get('ficha')
            datos_usuario.jornada = request.POST.get('jornada')

        foto_nueva = request.FILES.get('foto')

        if foto_nueva:
            if datos_usuario.foto:
                try:
                    if default_storage.exists(datos_usuario.foto.name):
                        default_storage.delete(datos_usuario.foto.name)
                except Exception as e:
                    print(f"⚠ Error al eliminar foto antigua: {e}")

            datos_usuario.foto = foto_nueva

        try:
            datos_usuario.save()
            messages.success(request, "Perfil actualizado correctamente")
        except Exception as e:
            # Agregar más información para debugging
            import traceback
            print(f"⚠ Error completo: {e}")
            print(f"⚠ Traceback: {traceback.format_exc()}")
            
            # Si el error es el vacío (0, ''), ignorarlo si los datos se guardaron
            if str(e) == "(0, '')":
                messages.success(request, "Perfil actualizado correctamente")
            else:
                messages.error(request, f"Error al guardar el perfil: {str(e)}")
        
        return redirect('perfil:perfiles')
    
    context = {'usuario': datos_usuario, 'tipo_perfil': tipo_perfil}
    return render(request, 'editar_perfil.html', context)


# ========================================
# VISTA: ELIMINAR PERFIL
# ========================================
@sesion_requerida
def eliminar_perfil(request):
    """Eliminar la cuenta del usuario"""
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

        logout(request)
        datos_usuario.delete()
        messages.success(request, "Cuenta eliminada correctamente")
        return redirect('sesion:home')

    return render(request, 'eliminar_perfil.html')

@sesion_requerida
@require_POST
def actualizar_privacidad(request):
    """
    Recibe JSON con los campos de privacidad y los guarda.
    Solo el propio usuario puede actualizar su privacidad.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=401)
 
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
 
    CAMPOS_PERMITIDOS = [
        'mostrar_email', 'mostrar_documento', 'mostrar_centro',
        'mostrar_region', 'mostrar_ficha', 'mostrar_jornada',
    ]
 
    privacidad = PrivacidadPerfil.obtener_o_crear(usuario_id)
 
    for campo in CAMPOS_PERMITIDOS:
        if campo in body:
            setattr(privacidad, campo, bool(body[campo]))
 
    privacidad.save()
    return JsonResponse({'ok': True})
 

# ========================================
# VISTA: VER PERFIL DE CUALQUIER USUARIO
# ========================================
@sesion_requerida
def ver_perfil(request, documento):
    usuario_actual_id = request.session.get('usuario_id')
    tipo_actual = request.session.get('tipo_usuario')

    usuario_actual_str = str(usuario_actual_id).strip() if usuario_actual_id else ''
    documento_str = str(documento).strip()

    print(f"\n{'='*70}")
    print(f"👤 VER PERFIL | actual: {usuario_actual_str} | viendo: {documento_str}")

    if usuario_actual_str and usuario_actual_str == documento_str:
        print(f"✅ Perfil propio → redirigiendo")
        return redirect('perfil:perfiles')

    # ✅ Obtener usuario y ct para likes
    usuario_like, ct_like = get_usuario_actual(request.session)

    usuario_perfil = None
    tipo_perfil = None

    try:
        if Aprendiz.objects.filter(numero_documento=documento_str).exists():
            usuario_perfil = Aprendiz.objects.get(numero_documento=documento_str)
            tipo_perfil = 'aprendiz'
        elif Instructor.objects.filter(numero_documento=documento_str).exists():
            usuario_perfil = Instructor.objects.get(numero_documento=documento_str)
            tipo_perfil = 'instructor'
        elif Bienestar.objects.filter(numero_documento=documento_str).exists():
            usuario_perfil = Bienestar.objects.get(numero_documento=documento_str)
            tipo_perfil = 'bienestar'
        else:
            messages.error(request, '❌ Usuario no encontrado.')
            return redirect('sesion:home')
    except Exception as e:
        print(f"❌ Error: {e}")
        messages.error(request, '❌ Error al cargar el perfil.')
        return redirect('sesion:home')

    try:
        usuario_obj = Usuario.objects.get(documento=documento_str)
    except Usuario.DoesNotExist:
        usuario_obj = None

    es_amigo = False
    solicitud_pendiente = False
    solicitud_enviada = False
    solicitud_id = None

    if usuario_obj:
        try:
            usuario_actual_obj = Usuario.objects.get(documento=usuario_actual_str)
            es_amigo = Amistad.son_amigos(usuario_actual_obj, usuario_obj)

            solicitud_recibida = Amistad.objects.filter(
                emisor=usuario_obj,
                receptor=usuario_actual_obj,
                estado=Amistad.PENDIENTE
            ).first()

            if solicitud_recibida:
                solicitud_pendiente = True
                solicitud_id = solicitud_recibida.id

            solicitud_enviada = Amistad.objects.filter(
                emisor=usuario_actual_obj,
                receptor=usuario_obj,
                estado=Amistad.PENDIENTE
            ).exists()

        except Usuario.DoesNotExist:
            pass
        except Exception as e:
            print(f"⚠️ Error amistad: {e}")

    publicaciones = None
    mostrar_publicaciones = False

    if tipo_perfil == 'bienestar':
        try:
            publicaciones = Publicacion.objects.filter(
                autor__numero_documento=documento_str,
                activa=True
            ).prefetch_related('archivos', 'comentarios', 'likes').order_by('-fecha_creacion')

            mostrar_publicaciones = True
            print(f"✅ Publicaciones: {publicaciones.count()}")

            # ✅ Anotar likes CORRECTAMENTE
            for pub in publicaciones:
                pub.yo_di_like = usuario_dio_like(pub, usuario_like, ct_like)

        except Exception as e:
            print(f"⚠️ Error publicaciones: {e}")
            publicaciones = None

    amigos = []
    if usuario_obj:
        try:
            amigos = Amistad.obtener_amigos(usuario_obj)
        except Exception as e:
            print(f"⚠️ Error amigos: {e}")
            amigos = []

    print(f"{'='*70}\n")

    usuario_unificado = Usuario.objects.get(documento=request.session['usuario_id'])
    privacidad = PrivacidadPerfil.obtener_o_crear(documento_str)

    # ✅ Obtener datos_usuario para el header (usuario logueado)

    context = {
        'usuario_perfil': usuario_perfil,
        'tipo_perfil': tipo_perfil,
        'usuario_obj': usuario_obj,
        'usuario': usuario_like,
        'publicaciones': publicaciones,
        'mostrar_publicaciones': mostrar_publicaciones,
        'es_amigo': es_amigo,
        'solicitud_pendiente': solicitud_pendiente,
        'solicitud_enviada': solicitud_enviada,
        'solicitud_id': solicitud_id,
        'amigos': amigos,
        'cantidad_amigos': len(amigos),
        'cantidad_publicaciones': publicaciones.count() if publicaciones else 0,
        'es_admin': usuario_unificado.es_admin,
        'priv_email': privacidad.mostrar_email,
        'priv_documento': privacidad.mostrar_documento,
        'priv_centro': privacidad.mostrar_centro,
        'priv_region': privacidad.mostrar_region,
        'priv_ficha': privacidad.mostrar_ficha,
        'priv_jornada': privacidad.mostrar_jornada,
    }

    return render(request, 'ver_perfil.html', context)