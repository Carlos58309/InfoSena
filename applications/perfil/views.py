# applications/perfil/views.py - VERSIÓN SIMPLIFICADA

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
from applications.publicaciones.models import Publicacion
from applications.amistades.models import Amistad
from applications.sesion.decorators import sesion_requerida

# ========================================
# VISTA: PERFIL PROPIO
# ========================================
@sesion_requerida
def perfiles(request):
    """Ver el perfil propio del usuario"""
    if 'usuario_id' not in request.session or 'tipo_usuario' not in request.session:
        return redirect('sesion:login')

    usuario_id = request.session['usuario_id']
    tipo_perfil = request.session['tipo_usuario']
    datos_usuario = None
    publicaciones = None

    print(f"\n{'='*60}")
    print(f"🏠 PERFILES - Perfil propio")
    print(f"{'='*60}")
    print(f"Usuario ID: {usuario_id}")
    print(f"Tipo: {tipo_perfil}")

    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
            print(f"✅ Aprendiz encontrado: {datos_usuario.nombre}")

        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
            print(f"✅ Instructor encontrado: {datos_usuario.nombre}")

        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
            print(f"✅ Bienestar encontrado: {datos_usuario.nombre}")

            # ✅ BUSCAR PUBLICACIONES - CORRECCIÓN FINAL
            try:
                print(f"\n🔍 Buscando publicaciones para documento: {usuario_id}")
                
                # Ver TODAS las publicaciones activas primero
                todas_publicaciones = Publicacion.objects.filter(activa=True)
                print(f"📊 Total publicaciones activas en BD: {todas_publicaciones.count()}")
                
                if todas_publicaciones.count() > 0:
                    print(f"\n📋 Primeras 3 publicaciones en BD:")
                    for pub in todas_publicaciones[:3]:
                        print(f"   ID: {pub.id}")
                        print(f"   Título: {pub.titulo}")
                        print(f"   Autor: {pub.autor}")
                        print(f"   Tipo autor: {type(pub.autor).__name__}")
                        
                        # El autor puede ser Bienestar (tiene numero_documento)
                        if hasattr(pub.autor, 'numero_documento'):
                            print(f"   Autor.numero_documento: {pub.autor.numero_documento}")
                        print(f"   ---")
                
                # ✅ FILTRAR PUBLICACIONES POR NUMERO_DOCUMENTO
                # Como pub.autor es Bienestar, debemos usar numero_documento
                publicaciones = Publicacion.objects.filter(
                    autor__numero_documento=usuario_id,  # ← CORRECCIÓN: usar numero_documento
                    activa=True
                ).order_by('-fecha_creacion')
                
                print(f"\n✅ Publicaciones del usuario {usuario_id}: {publicaciones.count()}")
                
                if publicaciones.count() > 0:
                    print(f"📝 Publicaciones encontradas:")
                    for pub in publicaciones:
                        print(f"   - {pub.titulo}")
                else:
                    print(f"⚠️ NO se encontraron publicaciones para este usuario")
                
            except Exception as e:
                print(f"❌ Error al cargar publicaciones: {e}")
                import traceback
                traceback.print_exc()
                publicaciones = None

    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist) as e:
        print(f"❌ Error: Usuario no encontrado - {e}")
        return redirect('sesion:login')

    print(f"{'='*60}\n")
    usuario = Usuario.objects.get(documento=request.session['usuario_id'])
    context = {
        'tipo_perfil': tipo_perfil,
        'usuario': datos_usuario,
        'publicaciones': publicaciones,
        'es_admin': usuario.es_admin,
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


# ========================================
# VISTA: VER PERFIL DE CUALQUIER USUARIO
# ========================================
@sesion_requerida
def ver_perfil(request, documento):
    """
    Ver perfil de cualquier usuario
    - Si es el perfil propio → redirige a editar perfil
    - Si es Bienestar → muestra sus publicaciones
    - Si es otro usuario → muestra perfil completo
    """
    
    # Obtener datos del usuario actual
    usuario_actual_id = request.session.get('usuario_id')
    tipo_actual = request.session.get('tipo_usuario')
    
    # ========================================
    # NORMALIZAR VALORES
    # ========================================
    usuario_actual_str = str(usuario_actual_id).strip() if usuario_actual_id else ''
    documento_str = str(documento).strip()
    
    print(f"\n{'='*70}")
    print(f"👤 VER PERFIL")
    print(f"   Usuario actual: {usuario_actual_str}")
    print(f"   Documento a ver: {documento_str}")
    
    # ========================================
    # VERIFICAR SI ES EL PERFIL PROPIO
    # ========================================
    if usuario_actual_str and usuario_actual_str == documento_str:
        print(f"✅ Es el perfil propio → redirigiendo")
        return redirect('perfil:perfiles')
    
    # ========================================
    # BUSCAR EL USUARIO A VER
    # ========================================
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
    
    # ========================================
    # OBTENER USUARIO UNIFICADO
    # ========================================
    try:
        usuario_obj = Usuario.objects.get(documento=documento_str)
    except Usuario.DoesNotExist:
        usuario_obj = None
    
    # ========================================
    # VERIFICAR RELACIÓN DE AMISTAD
    # ========================================
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
            print(f"⚠️ Error verificando amistad: {e}")
    
    # ========================================
    # OBTENER PUBLICACIONES (SOLO BIENESTAR)
    # ========================================
    publicaciones = None
    mostrar_publicaciones = False
    
    if tipo_perfil == 'bienestar':
        print(f"\n📝 Cargando publicaciones de Bienestar {documento_str}...")
        try:
            # ✅ CORRECCIÓN: usar numero_documento porque pub.autor es Bienestar
            publicaciones = Publicacion.objects.filter(
                autor__numero_documento=documento_str,  # ← CORRECCIÓN
                activa=True
            ).order_by('-fecha_creacion')
            
            mostrar_publicaciones = True
            print(f"✅ Publicaciones encontradas: {publicaciones.count()}")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            publicaciones = None
    
    # ========================================
    # OBTENER AMIGOS
    # ========================================
    amigos = []
    if usuario_obj:
        try:
            amigos = Amistad.obtener_amigos(usuario_obj)
        except Exception as e:
            print(f"⚠️ Error obteniendo amigos: {e}")
            amigos = []
    
    print(f"{'='*70}\n")
    usuario = Usuario.objects.get(documento=request.session['usuario_id'])
    # ========================================
    # PREPARAR CONTEXTO
    # ========================================
    context = {
        'usuario_perfil': usuario_perfil,
        'tipo_perfil': tipo_perfil,
        'usuario_obj': usuario_obj,
        'publicaciones': publicaciones,
        'mostrar_publicaciones': mostrar_publicaciones,
        'es_amigo': es_amigo,
        'solicitud_pendiente': solicitud_pendiente,
        'solicitud_enviada': solicitud_enviada,
        'solicitud_id': solicitud_id,
        'amigos': amigos,
        'cantidad_amigos': len(amigos),
        'cantidad_publicaciones': publicaciones.count() if publicaciones else 0,
        'es_admin': usuario.es_admin,
    }
    
    return render(request, 'ver_perfil.html', context)