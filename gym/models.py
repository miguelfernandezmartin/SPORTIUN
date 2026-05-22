from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('admin', 'Admin'),
        ('entrenador', 'Entrenador'),
        ('cliente', 'Cliente'),
    ]
    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')
    descripcion = models.TextField(blank=True)
    objetivo = models.CharField(max_length=300, blank=True)
    actualmente_entrenando = models.BooleanField(default=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='kg')
    altura = models.PositiveIntegerField(null=True, blank=True, help_text='cm')
    nivel_experiencia = models.CharField(max_length=20, choices=NIVEL_CHOICES, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    entrenador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Rutina(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rutinas')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} - {self.usuario.username}"

    @property
    def total_ejercicios(self):
        return Ejercicio.objects.filter(dia_rutina__rutina=self).count()


DIAS_SEMANA = [
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


class DiaRutina(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='dias')
    dia = models.IntegerField(choices=DIAS_SEMANA)
    nombre = models.CharField(max_length=100, blank=True, help_text='Ej: Push, Piernas, Torso')

    class Meta:
        ordering = ['dia']
        unique_together = [('rutina', 'dia')]

    def __str__(self):
        dia_nombre = dict(DIAS_SEMANA).get(self.dia, '')
        if self.nombre:
            return f"{dia_nombre} — {self.nombre}"
        return dia_nombre


class EjercicioCatalogo(models.Model):
    wger_id = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    musculo_principal = models.CharField(max_length=100, blank=True)
    equipamiento = models.CharField(max_length=100, blank=True)
    imagen_url = models.URLField(blank=True, max_length=500)
    fecha_importacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Ejercicio del catálogo'
        verbose_name_plural = 'Catálogo de ejercicios'

    def __str__(self):
        return self.nombre


class Ejercicio(models.Model):
    dia_rutina = models.ForeignKey(
        DiaRutina,
        on_delete=models.CASCADE,
        related_name='ejercicios',
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=200)
    series = models.PositiveIntegerField(default=3)
    repeticiones = models.PositiveIntegerField(default=10)
    peso_sugerido = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='kg')
    descanso = models.PositiveIntegerField(null=True, blank=True, help_text='segundos entre series')
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.series}x{self.repeticiones}"


class Sesion(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sesiones')
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='sesiones')
    dia_rutina = models.ForeignKey(DiaRutina, on_delete=models.CASCADE, related_name='sesiones')
    fecha = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.cliente.username} - {self.dia_rutina} - {self.fecha.date()}"


class EjercicioRegistrado(models.Model):
    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='ejercicios_registrados')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    series_completadas = models.PositiveIntegerField()
    repeticiones_realizadas = models.PositiveIntegerField()
    peso_utilizado = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='kg')
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.ejercicio.nombre} - {self.sesion.fecha.date()}"


class FeedbackEntrenador(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_recibido')
    entrenador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_dado')
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='feedback')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Feedback para {self.cliente.username} - {self.fecha_creacion.date()}"
