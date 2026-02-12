# applications/chat/admin.py
from django.contrib import admin
from .models import Chat, Mensaje, MensajeVisto


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'es_grupo', 'nombre_mostrar', 'cantidad_participantes', 'cantidad_mensajes', 'creado_en')
    list_filter = ('is_group', 'creado_en')
    search_fields = ('nombre_grupo', 'participantes__nombre')
    filter_horizontal = ('participantes',)
    readonly_fields = ('creado_en', 'actualizado_en')
    
    fieldsets = (
        ('Información General', {
            'fields': ('is_group', 'participantes')
        }),
        ('Información de Grupo', {
            'fields': ('nombre_grupo', 'descripcion_grupo', 'foto_grupo', 'admin_grupo'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def es_grupo(self, obj):
        return "✅ Sí" if obj.is_group else "❌ No"
    es_grupo.short_description = 'Es Grupo'
    
    def nombre_mostrar(self, obj):
        if obj.is_group:
            return f"🏢 {obj.nombre_grupo}"
        else:
            participantes = obj.participantes.all()[:2]
            return f"💬 {' y '.join([p.nombre for p in participantes])}"
    nombre_mostrar.short_description = 'Nombre'
    
    def cantidad_participantes(self, obj):
        return obj.participantes.count()
    cantidad_participantes.short_description = 'Participantes'
    
    def cantidad_mensajes(self, obj):
        return obj.mensajes.count()
    cantidad_mensajes.short_description = 'Mensajes'


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_info', 'autor', 'contenido_preview', 'visto', 'enviado')
    list_filter = ('visto', 'enviado', 'chat__is_group')
    search_fields = ('contenido', 'autor__nombre', 'chat__nombre_grupo')
    readonly_fields = ('enviado', 'editado', 'visto_en')
    date_hierarchy = 'enviado'
    
    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('chat', 'autor', 'contenido')
        }),
        ('Archivo Adjunto', {
            'fields': ('archivo', 'tipo_archivo'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('visto', 'visto_en', 'enviado', 'editado')
        }),
    )
    
    def chat_info(self, obj):
        if obj.chat.is_group:
            return f"🏢 {obj.chat.nombre_grupo}"
        else:
            return "💬 Chat individual"
    chat_info.short_description = 'Chat'
    
    def contenido_preview(self, obj):
        return obj.contenido[:50] + "..." if len(obj.contenido) > 50 else obj.contenido
    contenido_preview.short_description = 'Contenido'


@admin.register(MensajeVisto)
class MensajeVistoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mensaje_info', 'usuario', 'visto_en')
    list_filter = ('visto_en',)
    search_fields = ('usuario__nombre', 'mensaje__contenido')
    readonly_fields = ('visto_en',)
    date_hierarchy = 'visto_en'
    
    def mensaje_info(self, obj):
        preview = obj.mensaje.contenido[:30] + "..." if len(obj.mensaje.contenido) > 30 else obj.mensaje.contenido
        return f"Mensaje {obj.mensaje.id}: {preview}"
    mensaje_info.short_description = 'Mensaje'