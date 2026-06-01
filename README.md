# SPORTIUN — Own It

> Plataforma web completa de gestión de entrenamiento personal.  
> **Entrena. Registra. Evoluciona. Supérate.**

---

## ¿Qué es SPORTIUN?

SPORTIUN es una aplicación web desarrollada con Django que permite gestionar de forma integral el entrenamiento físico. Conecta a clientes y entrenadores en una misma plataforma, cubriendo todo el ciclo: diseño de rutinas → ejecución de sesiones → seguimiento del progreso → feedback del entrenador.

**Autores:** Diego Rivas · Miguel Fernández · Adrián Carrasco  
**Contexto:** Trabajo de Fin de Grado

---

## Funcionalidades principales

### Vista del cliente
- Registro, login y perfil con datos físicos (peso, altura, nivel, objetivo)
- Selector de rol (cliente / entrenador) desde el propio perfil
- Asignación de entrenador directamente desde el perfil
- Creación y gestión de rutinas semanales con días nombrados (Push, Pull, Piernas…)
- Catálogo de +800 ejercicios con filtros por músculo, equipamiento y categoría
- Registro de sesiones de entrenamiento: **cada serie con su propio peso y repeticiones**
- Historial de sesiones paginado con gráfica de volumen total (Chart.js)
- Vista de progreso con gráficas de evolución de peso y volumen por ejercicio
- Pestaña de feedback recibido del entrenador dentro de Sesiones
- Asistente IA de entrenamiento (chatbot powered by Claude Sonnet)

### Vista del entrenador
- Panel con estadísticas globales (clientes, sesiones totales y completadas)
- Lista de clientes con buscador
- Ficha de cliente con 4 pestañas: Rutinas · Entrenamientos · Progreso · Feedback
- Asignación de rutinas: clona cualquier rutina propia al espacio del cliente
- Visualización completa del historial de sesiones del cliente con series individuales
- Gráfica de volumen del cliente
- Envío de feedback vinculado a una rutina concreta

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 5+ · Django REST Framework |
| Frontend | Bootstrap 5 · Django Templates · Chart.js |
| Base de datos | SQLite (desarrollo) |
| Catálogo ejercicios | [Wger API](https://wger.de/api/v2/) — +800 ejercicios |
| Despliegue | [Render](https://render.com) — conectado a GitHub |
| IA Chatbot | [Ollama](https://ollama.com) — corriendo en local |

---

## Modelos de datos

```
User (Django)
├── PerfilUsuario       — rol, datos físicos, entrenador asignado
├── Rutina
│   └── DiaRutina       — día de la semana + nombre (Push, Pull…)
│       └── Ejercicio   — nombre, series, reps, peso sugerido, descanso
└── Sesion              — día de entrenamiento registrado
    └── EjercicioRegistrado
        └── SerieRegistrada  — numero_serie, repeticiones, peso

FeedbackEntrenador      — mensaje del entrenador vinculado a cliente + rutina
EjercicioCatalogo       — ejercicios importados desde Wger
```

---

## Instalación y ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/SPORTIUN.git
cd SPORTIUN
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario

```bash
python manage.py createsuperuser
```

### 6. (Opcional) Importar catálogo de ejercicios

Requiere conexión a internet. El comando es idempotente (se puede ejecutar varias veces sin duplicar datos).

```bash
# Con traducción automática al español (más lento, requiere deep-translator)
pip install deep-translator
python manage.py importar_ejercicios

# Sin traducción (más rápido)
python manage.py importar_ejercicios --sin-traducir

# Importación parcial para pruebas
python manage.py importar_ejercicios --limite 50
```

### 7. Arrancar el servidor

```bash
python manage.py runserver
```

Abre **http://127.0.0.1:8000** en el navegador.  
Panel de administración: **http://127.0.0.1:8000/admin/**

---

## Configurar el chatbot IA (opcional)

El chatbot requiere una API key de Anthropic. Añade en `rutinas_gym/settings.py`:

```python
ANTHROPIC_API_KEY = 'sk-ant-...'
```

O como variable de entorno:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

Sin API key, el chatbot muestra un aviso informativo y el resto de la app funciona con normalidad.

---

## Despliegue en Render

El repositorio incluye `render.yaml` con la configuración lista. Pasos:

1. Sube el proyecto a GitHub
2. Crea un nuevo **Web Service** en [render.com](https://render.com) conectado al repo
3. Añade la variable de entorno `DJANGO_SECRET_KEY` (genera una con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
4. Añade `ANTHROPIC_API_KEY` si quieres el chatbot activo
5. Render ejecutará automáticamente `pip install`, `collectstatic` y `migrate`

---

## Rutas principales

| URL | Descripción |
|-----|-------------|
| `/` | Landing page |
| `/gym/` | Lista de rutinas del usuario |
| `/gym/rutina/<id>/` | Detalle de rutina con días y ejercicios |
| `/gym/catalogo/` | Catálogo de ejercicios con filtros |
| `/gym/dia/<id>/entrenar/` | Iniciar sesión de entrenamiento |
| `/gym/historial/` | Historial de sesiones + feedback recibido |
| `/gym/progreso/` | Gráficas de progreso personal |
| `/gym/perfil/` | Perfil de usuario |
| `/gym/chatbot/` | Asistente IA de entrenamiento |
| `/gym/entrenador/` | Panel del entrenador |
| `/gym/entrenador/clientes/` | Lista de clientes |
| `/gym/entrenador/cliente/<id>/` | Ficha detallada del cliente |
| `/admin/` | Panel de administración Django |

---

## Usuarios de prueba (desarrollo)

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Cliente | AlbertoAbellan | Aula17++ |
| Superusuario | miguel | Aula17++ |

> Para cambiar el rol de un usuario a `entrenador`: entra a tu perfil → campo "Soy…" → selecciona Entrenador → Guardar.  
> Para asignar un cliente a un entrenador: el cliente entra a su perfil y selecciona su entrenador en el campo "Mi entrenador".

---

## Estructura del proyecto

```
SPORTIUN/
├── core/                    # App de autenticación (registro, login)
│   └── templates/
├── gym/                     # App principal
│   ├── management/commands/ # importar_ejercicios
│   ├── migrations/
│   ├── templates/gym/       # Todos los templates de la app
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── base.html
├── rutinas_gym/             # Configuración Django
│   └── settings.py
├── requirements.txt
└── render.yaml
```

---

## Licencia

Proyecto académico — Trabajo de Fin de Grado.
