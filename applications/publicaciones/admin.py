from django.contrib import admin
from .models import Publicacion, ArchivoPublicacion, Like, Comentario


class ArchivoPublicacionInline(admin.TabularInline):
    """
    Inline para mostrar los archivos dentro de la publicación
    """
    model = ArchivoPublicacion
    extra = 1
    fields = ('tipo', 'archivo', 'orden')
    readonly_fields = ('fecha_subida',)


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'categoria', 'fecha_creacion', 'activa', 'total_likes', 'total_comentarios')
    list_filter = ('categoria', 'activa', 'fecha_creacion')
    search_fields = ('titulo', 'contenido', 'autor__nombre')
    date_hierarchy = 'fecha_creacion'
    inlines = [ArchivoPublicacionInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('autor', 'titulo', 'contenido', 'categoria')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def total_likes(self, obj):
        return obj.total_likes()
    total_likes.short_description = 'Likes'
    
    def total_comentarios(self, obj):
        return obj.total_comentarios()
    total_comentarios.short_description = 'Comentarios'


@admin.register(ArchivoPublicacion)
class ArchivoPublicacionAdmin(admin.ModelAdmin):
    list_display = ('publicacion', 'tipo', 'archivo', 'orden', 'fecha_subida')
    list_filter = ('tipo', 'fecha_subida')
    search_fields = ('publicacion__titulo',)
    list_editable = ('orden',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'publicacion', 'creado')
    list_filter = ('creado',)
    search_fields = ('usuario__nombre', 'publicacion__titulo')
    date_hierarchy = 'creado'


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('autor', 'publicacion', 'contenido_corto', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('autor__nombre', 'publicacion__titulo', 'contenido')
    date_hierarchy = 'fecha_creacion'
    
    def contenido_corto(self, obj):
        return obj.contenido[:50] + '...' if len(obj.contenido) > 50 else obj.contenido
    contenido_corto.short_description = 'Contenido'