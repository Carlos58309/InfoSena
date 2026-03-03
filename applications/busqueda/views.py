# applications/busqueda/views.py
# VISTAS MEJORADAS PARA LA BÚSQUEDA DE USUARIOS

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from applications.usuarios.models import Usuario
from applications.registro.models import Aprendiz, Instructor, Bienestar
import json


def obtener_usuario_actual(request):
    """
    Helper para obtener el Usuario actual desde la sesión
    """
    usuario_id = request.session.get('usuario_id')
    tipo_perfil = request.session.get('tipo_usuario')
    
    if not usuario_id or not tipo_perfil:
        return None
    
    try:
        if tipo_perfil == 'aprendiz':
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'instructor':
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == 'bienestar':
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            return None
    except (Aprendiz.DoesNotExist, Instructor.DoesNotExist, Bienestar.DoesNotExist):
        return None
    
    try:
        usuario_actual = Usuario.objects.get(documento=datos_usuario.numero_documento)
        return usuario_actual
    except Usuario.DoesNotExist:
        return None



@require_http_methods(["GET"])
def buscar_usuarios(request):
    """
    API para buscar usuarios por nombre o documento
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'resultados': []})
    
    # Buscar en Usuario
    usuarios = Usuario.objects.filter(
        nombre__icontains=query
    ) | Usuario.objects.filter(
        documento__icontains=query
    )
    
    # Limitar a 10 resultados
    usuarios = usuarios.distinct()[:10]
    
    resultados = []
    for usuario in usuarios:
        # Obtener información adicional del perfil
        ficha = None
        if usuario.tipo == 'aprendiz':
            try:
                aprendiz = Aprendiz.objects.get(numero_documento=usuario.documento)
                ficha = aprendiz.ficha
            except Aprendiz.DoesNotExist:
                pass
        
        # Determinar el tipo display
        tipo_display = {
            'aprendiz': 'Aprendiz',
            'instructor': 'Instructor',
            'bienestar': 'Bienestar al Aprendiz'
        }.get(usuario.tipo, 'Usuario')
        
        resultados.append({
            'id': usuario.id,
            'nombre': usuario.nombre,
            'tipo': usuario.tipo,
            'tipo_display': tipo_display,
            'documento': usuario.documento,
            'foto': usuario.foto.url if usuario.foto else None,
            'ficha': ficha
        })
    
    return JsonResponse({'resultados': resultados})



@require_http_methods(["GET"])
def obtener_historial(request):
    """
    Obtener el historial de búsquedas del usuario
    """
    usuario_actual = obtener_usuario_actual(request)
    
    if not usuario_actual:
        return JsonResponse({'historial': []})
    
    # Obtener historial desde la sesión
    historial_ids = request.session.get('busqueda_historial', [])
    
    if not historial_ids:
        return JsonResponse({'historial': []})
    
    # Obtener usuarios del historial
    usuarios = Usuario.objects.filter(id__in=historial_ids)
    
    # Ordenar según el orden en historial_ids
    usuarios_ordenados = []
    for user_id in historial_ids:
        for usuario in usuarios:
            if usuario.id == user_id:
                usuarios_ordenados.append(usuario)
                break
    
    resultados = []
    for usuario in usuarios_ordenados[:10]:  # Limitar a 10
        tipo_display = {
            'aprendiz': 'Aprendiz',
            'instructor': 'Instructor',
            'bienestar': 'Bienestar al Aprendiz'
        }.get(usuario.tipo, 'Usuario')
        
        resultados.append({
            'id': usuario.id,
            'nombre': usuario.nombre,
            'tipo': usuario.tipo,
            'tipo_display': tipo_display,
            'documento': usuario.documento,
            'foto': usuario.foto.url if usuario.foto else None,
        })
    
    return JsonResponse({'historial': resultados})



@require_http_methods(["POST"])
def guardar_en_historial(request):
    """
    Guardar una búsqueda en el historial
    """
    try:
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        
        if not usuario_id:
            return JsonResponse({'error': 'Usuario ID requerido'}, status=400)
        
        # Obtener historial actual
        historial = request.session.get('busqueda_historial', [])
        
        # Eliminar si ya existe (para moverlo al principio)
        if usuario_id in historial:
            historial.remove(usuario_id)
        
        # Agregar al principio
        historial.insert(0, usuario_id)
        
        # Limitar a 20 elementos
        historial = historial[:20]
        
        # Guardar en sesión
        request.session['busqueda_historial'] = historial
        request.session.modified = True
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@require_http_methods(["POST"])
def eliminar_del_historial(request):
    """
    Eliminar un usuario del historial
    """
    try:
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        
        if not usuario_id:
            return JsonResponse({'error': 'Usuario ID requerido'}, status=400)
        
        # Obtener historial actual
        historial = request.session.get('busqueda_historial', [])
        
        # Eliminar el usuario
        if usuario_id in historial:
            historial.remove(usuario_id)
        
        # Guardar en sesión
        request.session['busqueda_historial'] = historial
        request.session.modified = True
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@require_http_methods(["POST"])
def limpiar_historial(request):
    """
    Limpiar todo el historial de búsquedas
    """
    try:
        request.session['busqueda_historial'] = []
        request.session.modified = True
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@require_http_methods(["GET"])
def obtener_documento_usuario(request, usuario_id):
    """
    ✅ NUEVA VISTA: Obtener el documento de un usuario por su ID
    Necesario para redirigir correctamente al perfil
    """
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        return JsonResponse({
            'documento': usuario.documento,
            'tipo': usuario.tipo,
            'nombre': usuario.nombre
        })
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)