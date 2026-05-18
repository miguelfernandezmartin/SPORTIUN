from django.urls import path
from . import views

app_name = 'gym'

urlpatterns = [
    path('', views.rutinas_list, name='rutinas_list'),
    path('rutina/crear/', views.crear_rutina, name='crear_rutina'),
    path('rutina/<int:rutina_id>/', views.detalle_rutina, name='detalle_rutina'),
    path('rutina/<int:rutina_id>/eliminar/', views.eliminar_rutina, name='eliminar_rutina'),
    path('rutina/<int:rutina_id>/dia/crear/', views.crear_dia, name='crear_dia'),
    path('dia/<int:dia_id>/eliminar/', views.eliminar_dia, name='eliminar_dia'),
    path('dia/<int:dia_id>/ejercicio/crear/', views.crear_ejercicio, name='crear_ejercicio'),
    path('ejercicio/<int:ejercicio_id>/eliminar/', views.eliminar_ejercicio, name='eliminar_ejercicio'),
    path('perfil/', views.perfil, name='perfil'),
    path('catalogo/', views.catalogo_ejercicios, name='catalogo_ejercicios'),
    path('catalogo/<int:catalogo_id>/anadir/<int:dia_id>/', views.anadir_desde_catalogo, name='anadir_desde_catalogo'),
]
