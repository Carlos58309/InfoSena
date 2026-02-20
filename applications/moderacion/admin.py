# applications/moderacion/admin.py
"""
Panel de administración para moderación
"""

from django.contrib import admin
from .models import RegistroModeracion, UsuarioSancionado, PalabraProhibida


@admin.register(RegistroModeracion)
class RegistroModeracionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'usuario',
        'tipo_contenido',
        'resultado',
        'metodo_usado',
        'creado_en'
    ]
    list_filter = [
        'resultado',
        'tipo_contenido',
        'metodo_usado',
        'creado_en'
    ]
    search_fields = [
        'usuario__nombre',
        'contenido_texto',
        'razon'
    ]
    readonly_fields = [
        'creado_en',
        'score_confianza',
        'categorias_violadas'
    ]
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario', 'ip_address', 'user_agent')
        }),
        ('Contenido Moderado', {
            'fields': ('tipo_contenido', 'contenido_texto', 'archivo_url')
        }),
        ('Resultado', {
            'fields': (
                'resultado',
                'razon',
                'categorias_violadas',
                'score_confianza',
                'metodo_usado'
            )
        }),
        ('Metadata', {
            'fields': ('creado_en',)
        }),
    )
    
    def has_add_permission(self, request):
        # No permitir crear registros manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Solo lectura
        return False


@admin.register(UsuarioSancionado)
class UsuarioSancionadoAdmin(admin.ModelAdmin):
    list_display = [
        'usuario',
        'tipo_sancion',
        'activa',
        'fecha_inicio',
        'fecha_fin',
        'aplicada_por'
    ]
    list_filter = [
        'tipo_sancion',
        'activa',
        'fecha_inicio'
    ]
    search_fields = [
        'usuario__nombre',
        'razon'
    ]
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario', 'tipo_sancion', 'razon')
        }),
        ('Duración', {
            'fields': ('fecha_inicio', 'fecha_fin', 'activa')
        }),
        ('Moderación', {
            'fields': ('aplicada_por',)
        }),
    )
    
    actions = ['desactivar_sanciones', 'activar_sanciones']
    
    def desactivar_sanciones(self, request, queryset):
        queryset.update(activa=False)
        self.message_user(request, f"{queryset.count()} sanciones desactivadas")
    desactivar_sanciones.short_description = "Desactivar sanciones seleccionadas"
    
    def activar_sanciones(self, request, queryset):
        queryset.update(activa=True)
        self.message_user(request, f"{queryset.count()} sanciones activadas")
    activar_sanciones.short_description = "Activar sanciones seleccionadas"


@admin.register(PalabraProhibida)
class PalabraProhibidaAdmin(admin.ModelAdmin):
    list_display = [
        'palabra',
        'severidad',
        'activa',
        'creada_en'
    ]
    list_filter = [
        'severidad',
        'activa',
        'creada_en'
    ]
    search_fields = ['palabra']
    
    fieldsets = (
        ('Palabra', {
            'fields': ('palabra', 'severidad', 'activa')
        }),
        ('Metadata', {
            'fields': ('creada_en',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_palabras', 'desactivar_palabras']
    
    def activar_palabras(self, request, queryset):
        queryset.update(activa=True)
        self.message_user(request, f"{queryset.count()} palabras activadas")
    activar_palabras.short_description = "Activar palabras seleccionadas"
    
    def desactivar_palabras(self, request, queryset):
        queryset.update(activa=False)
        self.message_user(request, f"{queryset.count()} palabras desactivadas")
    desactivar_palabras.short_description = "Desactivar palabras seleccionadas"