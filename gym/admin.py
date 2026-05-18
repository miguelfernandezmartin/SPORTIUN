from django.contrib import admin
from .models import Rutina, Ejercicio, PerfilUsuario, DiaRutina, EjercicioCatalogo


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
    list_display = ['usuario', 'rol', 'nivel_experiencia', 'actualmente_entrenando', 'fecha_creacion']
    list_filter = ['rol', 'nivel_experiencia', 'actualmente_entrenando']
