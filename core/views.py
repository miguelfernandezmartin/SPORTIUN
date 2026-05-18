from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import RegistroForm

def inicio(request):
    """
    Renderiza la página de bienvenida principal de la aplicación.
    """
    return render(request, 'core/inicio.html')


def registro(request):
    """
    Gestiona el registro de nuevos usuarios.
    
    Al registrarse, el usuario inicia sesión automáticamente
    y es redirigido a su lista de rutinas.
    """
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}! Su cuenta ha sido creada.')
            return redirect('gym:rutinas_list')
    else:
        form = RegistroForm()

    return render(request, 'registro/register.html', {'form': form})


def login_usuario(request):
    """
    Gestiona el inicio de sesión de usuarios existentes.
    
    Utiliza AuthenticationForm para validar las credenciales.
    """
    if request.method == 'POST':
        # AuthenticationForm requiere el objeto request y los datos del POST
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
            
            return redirect('gym:rutinas_list')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()

    return render(request, 'registro/login.html', {'form': form})


def logout_usuario(request):
    """
    Hace logout a la sesion del usuario actual y redirige a la página de inicio.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('core:inicio')