# applications/busqueda/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from applications.registro.models import Aprendiz, Instructor, Bienestar
from applications.usuarios.models import Usuario
import json
import traceback


@require_http_methods(["GET"])
def buscar_usuarios(request):
    """
    Búsqueda de usuarios en tiempo real
    Retorna resultados en formato JSON
    """
    try:
        query = request.GET.get('q', '').strip()
        
        print(f"🔍 Búsqueda recibida: '{query}'")  # Debug
        
        if not query or len(query) < 2:
            print("❌ Query muy corto o vacío")
            return JsonResponse({'resultados': []})
        
        # Buscar en las 3 tablas (case-insensitive con __icontains)
        resultados = []
        
        # ===================================
        # BUSCAR EN APRENDICES
        # ===================================
        print("🔍 Buscando en Aprendices...")
        aprendices = Aprendiz.objects.filter(
            Q(nombre__icontains=query) | Q(numero_documento__icontains=query)
        )[:5]
        
        print(f"   Encontrados: {aprendices.count()} aprendices")
        
        for aprendiz in aprendices:
            resultados.append({
                'id': aprendiz.numero_documento,
                'nombre': aprendiz.nombre,
                'tipo': 'aprendiz',
                'tipo_display': 'Aprendiz',
                'foto': aprendiz.foto.url if aprendiz.foto else None,
                'email': aprendiz.email,
                'ficha': aprendiz.ficha if hasattr(aprendiz, 'ficha') else None,
            })
        
        # ===================================
        # BUSCAR EN INSTRUCTORES
        # ===================================
        print("🔍 Buscando en Instructores...")
        instructores = Instructor.objects.filter(
            Q(nombre__icontains=query) | Q(numero_documento__icontains=query)
        )[:5]
        
        print(f"   Encontrados: {instructores.count()} instructores")
        
        for instructor in instructores:
            resultados.append({
                'id': instructor.numero_documento,
                'nombre': instructor.nombre,
                'tipo': 'instructor',
                'tipo_display': 'Instructor',
                'foto': instructor.foto.url if instructor.foto else None,
                'email': instructor.email,
            })
        
        # ===================================
        # BUSCAR EN BIENESTAR
        # ===================================
        print("🔍 Buscando en Bienestar...")
        bienestar_usuarios = Bienestar.objects.filter(
            Q(nombre__icontains=query) | Q(numero_documento__icontains=query)
        )[:5]
        
        print(f"   Encontrados: {bienestar_usuarios.count()} usuarios de bienestar")
        
        for bienestar in bienestar_usuarios:
            resultados.append({
                'id': bienestar.numero_documento,
                'nombre': bienestar.nombre,
                'tipo': 'bienestar',
                'tipo_display': 'Bienestar',
                'foto': bienestar.foto.url if bienestar.foto else None,
                'email': bienestar.email,
            })
        
        # Limitar resultados totales
        resultados = resultados[:10]
        
        print(f"✅ Total de resultados: {len(resultados)}")
        
        return JsonResponse({
            'resultados': resultados,
            'total': len(resultados)
        })
    
    except Exception as e:
        print(f"❌ ERROR en buscar_usuarios: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'resultados': []
        }, status=500)


@require_http_methods(["POST"])
def guardar_busqueda(request):
    """
    Guarda una búsqueda en el historial del usuario
    """
    try:
        if 'usuario_id' not in request.session:
            print("⚠️ Usuario no autenticado")
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        
        print(f"💾 Guardando búsqueda: {nombre} ({tipo})")
        
        # Guardar en sesión (historial temporal)
        if 'historial_busqueda' not in request.session:
            request.session['historial_busqueda'] = []
        
        historial = request.session['historial_busqueda']
        
        # Crear entrada de historial
        entrada = {
            'usuario_id': usuario_id,
            'nombre': nombre,
            'tipo': tipo,
        }
        
        # Eliminar duplicados (si ya existe)
        historial = [h for h in historial if h['usuario_id'] != usuario_id]
        
        # Agregar al inicio
        historial.insert(0, entrada)
        
        # Mantener solo los últimos 10
        historial = historial[:10]
        
        request.session['historial_busqueda'] = historial
        request.session.modified = True
        
        print(f"✅ Búsqueda guardada. Total en historial: {len(historial)}")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        print(f"❌ ERROR en guardar_busqueda: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def obtener_historial(request):
    """
    Obtiene el historial de búsquedas del usuario
    """
    try:
        if 'usuario_id' not in request.session:
            print("⚠️ Usuario no autenticado para historial")
            return JsonResponse({'historial': []})
        
        historial = request.session.get('historial_busqueda', [])
        
        print(f"📜 Cargando historial: {len(historial)} entradas")
        
        # Enriquecer con datos actuales
        historial_enriquecido = []
        
        for item in historial:
            usuario_id = item.get('usuario_id')
            tipo = item.get('tipo')
            
            try:
                if tipo == 'aprendiz':
                    usuario = Aprendiz.objects.get(numero_documento=usuario_id)
                elif tipo == 'instructor':
                    usuario = Instructor.objects.get(numero_documento=usuario_id)
                elif tipo == 'bienestar':
                    usuario = Bienestar.objects.get(numero_documento=usuario_id)
                else:
                    continue
                
                historial_enriquecido.append({
                    'id': usuario_id,
                    'nombre': usuario.nombre,
                    'tipo': tipo,
                    'tipo_display': tipo.capitalize(),
                    'foto': usuario.foto.url if usuario.foto else None,
                })
            except Exception as inner_e:
                print(f"⚠️ Usuario en historial no encontrado: {usuario_id} - {inner_e}")
                continue
        
        print(f"✅ Historial enriquecido: {len(historial_enriquecido)} usuarios")
        
        return JsonResponse({'historial': historial_enriquecido})
    
    except Exception as e:
        print(f"❌ ERROR en obtener_historial: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'historial': []})


@require_http_methods(["POST"])
def eliminar_busqueda(request):
    """
    Elimina una búsqueda específica del historial
    """
    try:
        if 'usuario_id' not in request.session:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        
        print(f"🗑️ Eliminando del historial: {usuario_id}")
        
        historial = request.session.get('historial_busqueda', [])
        
        # Filtrar el elemento a eliminar
        historial = [h for h in historial if h['usuario_id'] != usuario_id]
        
        request.session['historial_busqueda'] = historial
        request.session.modified = True
        
        print(f"✅ Eliminado. Quedan {len(historial)} en historial")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        print(f"❌ ERROR en eliminar_busqueda: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def limpiar_historial(request):
    """
    Limpia todo el historial de búsquedas
    """
    try:
        if 'usuario_id' not in request.session:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        print("🗑️ Limpiando todo el historial")
        
        request.session['historial_busqueda'] = []
        request.session.modified = True
        
        print("✅ Historial limpiado")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        print(f"❌ ERROR en limpiar_historial: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)