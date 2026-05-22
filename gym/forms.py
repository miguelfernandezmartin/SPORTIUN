from django import forms
from .models import Ejercicio, Rutina, PerfilUsuario, DiaRutina, DIAS_SEMANA, FeedbackEntrenador


class EjercicioForm(forms.ModelForm):
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'series', 'repeticiones', 'peso_sugerido', 'descanso', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Press de banca con mancuernas'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3',
                'min': '1'
            }),
            'repeticiones': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10',
                'min': '1'
            }),
            'peso_sugerido': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 60',
                'min': '0',
                'step': '0.5'
            }),
            'descanso': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 90',
                'min': '0'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Controlar la bajada, codos a 45°'
            }),
        }
        labels = {
            'peso_sugerido': 'Peso sugerido (kg)',
            'descanso': 'Descanso entre series (segundos)',
        }


class RutinaForm(forms.ModelForm):
    class Meta:
        model = Rutina
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Empujes / Pierna / Torso...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Resumen de esta rutina'
            }),
        }


class DiaRutinaForm(forms.ModelForm):
    class Meta:
        model = DiaRutina
        fields = ['dia', 'nombre']
        widgets = {
            'dia': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Push, Piernas, Torso (opcional)'
            }),
        }
        labels = {
            'dia': 'Día de la semana',
            'nombre': 'Nombre del día',
        }


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = [
            'descripcion',
            'objetivo',
            'peso',
            'altura',
            'nivel_experiencia',
            'fecha_nacimiento',
            'actualmente_entrenando',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos un poco sobre tu trayectoria en el Gym'
            }),
            'objetivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ganancia muscular / Definición / Resistencia'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 75.5',
                'step': '0.1',
                'min': '30'
            }),
            'altura': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 175',
                'min': '100',
                'max': '250'
            }),
            'nivel_experiencia': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'actualmente_entrenando': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'peso': 'Peso (kg)',
            'altura': 'Altura (cm)',
            'nivel_experiencia': 'Nivel de experiencia',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'actualmente_entrenando': '¿Estás entrenando actualmente?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nivel_experiencia'].required = False


class FeedbackEntrenadorForm(forms.ModelForm):
    class Meta:
        model = FeedbackEntrenador
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escribe tu feedback o ajustes recomendados...'
            }),
        }
        labels = {
            'contenido': 'Feedback',
        }
