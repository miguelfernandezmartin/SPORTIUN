from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    """
    Formulario personalizado para el registro de nuevos usuarios.
    
    Hereda de UserCreationForm para aprovechar la lógica de creación de usuarios
    y validación de contraseñas de Django, añadiendo el campo email como obligatorio.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Introduzca su email'})
    )

    class Meta:
        """
        Configuración de metadatos del formulario.
        Define el modelo al cual esta vinculado y los campos que se mostrarán.
        """
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        }

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        # Accedo al diccionario de campos para añadir estilos
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})