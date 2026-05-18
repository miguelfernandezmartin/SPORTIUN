from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('',            views.inicio,           name='inicio'),
    path('registro/',   views.registro,         name='registro'),
    path('login/',      views.login_usuario,    name='login'),  
    path('logout/',     views.logout_usuario,   name='logout'),
]