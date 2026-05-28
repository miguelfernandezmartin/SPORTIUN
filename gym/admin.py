from django.contrib import admin
from .models import Rutina, Ejercicio, PerfilUsuario, DiaRutina, EjercicioCatalogo, Sesion, EjercicioRegistrado, SerieRegistrada, FeedbackEntrenador


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'fecha_creacion']
    list_filter = ['fecha_creacion', 'usuario']


@admin.register(DiaRutina)
class DiaRutinaAdmin(admin.ModelAdmin):
    list_display = ['rutina', 'dia', 'nombre']
    list_filter = ['dia']


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'dia_rutina', 'series', 'repeticiones', 'peso_sugerido']
    list_filter = ['dia_rutina__rutina']


@admin.register(EjercicioCatalogo)
class EjercicioCatalogoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'musculo_principal', 'equipamiento']
    list_filter = ['categoria', 'equipamiento']
    search_fields = ['nombre', 'musculo_principal']


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'nivel_experiencia', 'actualmente_entrenando', 'entrenador', 'fecha_creacion']
    list_filter = ['rol', 'nivel_experiencia', 'actualmente_entrenando']
    search_fields = ['usuario__username', 'entrenador__username']


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'rutina', 'dia_rutina', 'fecha', 'completada']
    list_filter = ['completada', 'fecha']
    search_fields = ['cliente__username']


class SerieRegistradaInline(admin.TabularInline):
    model = SerieRegistrada
    extra = 0
    fields = ['numero_serie', 'repeticiones', 'peso', 'notas']


@admin.register(EjercicioRegistrado)
class EjercicioRegistradoAdmin(admin.ModelAdmin):
    list_display = ['ejercicio', 'sesion']
    inlines = [SerieRegistradaInline]


@admin.register(SerieRegistrada)
class SerieRegistradaAdmin(admin.ModelAdmin):
    list_display = ['ejercicio_registrado', 'numero_serie', 'repeticiones', 'peso']
    list_filter = ['numero_serie']


@admin.register(FeedbackEntrenador)
class FeedbackEntrenadorAdmin(admin.ModelAdmin):
    list_display = ['entrenador', 'cliente', 'rutina', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    search_fields = ['entrenador__username', 'cliente__username']