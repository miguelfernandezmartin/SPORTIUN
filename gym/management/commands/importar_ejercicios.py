import html
import re
import time
import requests
from django.core.management.base import BaseCommand
from gym.models import EjercicioCatalogo

WGER_BASE = 'https://wger.de/api/v2'
LANG_EN = 2   # English
LANG_ES = 4   # Español

# Traducciones manuales para los campos fijos de la API (Filtros en Español)
CATEGORIAS_ES = {
    'Abs': 'Abdominales',
    'Arms': 'Brazos',
    'Back': 'Espalda',
    'Calves': 'Gemelos',
    'Cardio': 'Cardio',
    'Chest': 'Pecho',
    'Glutes': 'Glúteos',
    'Legs': 'Piernas',
    'Neck': 'Cuello',
    'Shoulders': 'Hombros',
}

MUSCULOS_ES = {
    'Anterior deltoid': 'Deltoides anterior',
    'Posterior deltoid': 'Deltoides posterior',
    'Middle deltoid': 'Deltoides medio',
    'Biceps brachii': 'Bíceps',
    'Brachialis': 'Braquial',
    'Triceps brachii': 'Tríceps',
    'Pectoralis major': 'Pectoral mayor',
    'Serratus anterior': 'Serrato anterior',
    'Latissimus dorsi': 'Dorsal ancho',
    'Trapezius': 'Trapecio',
    'Rhomboids': 'Romboides',
    'Infraspinatus': 'Infraespinoso',
    'Teres major': 'Redondo mayor',
    'Rectus abdominis': 'Recto abdominal',
    'Obliquus externus abdominis': 'Oblicuo externo',
    'Iliopsoas': 'Iliopsoas',
    'Quadriceps femoris': 'Cuádriceps',
    'Biceps femoris': 'Isquiotibiales',
    'Gluteus maximus': 'Glúteo mayor',
    'Gastrocnemius': 'Gemelos',
    'Soleus': 'Sóleo',
    'Tibialis anterior': 'Tibial anterior',
    'Adductor longus': 'Aductor largo',
    'Tensor fasciae latae': 'Tensor de la fascia lata',
    'Quads': 'Cuádriceps',
    'Hamstrings': 'Isquiotibiales',
    'Glutes': 'Glúteos',
    'Abs': 'Abdominales',
    'Shoulders': 'Hombros',
    'Chest': 'Pecho',
    'Biceps': 'Bíceps',
    'Triceps': 'Tríceps',
    'Calves': 'Gemelos',
    'Forearms': 'Antebrazos',
}

EQUIPAMIENTO_ES = {
    'Barbell': 'Barra',
    'Dumbbell': 'Mancuerna',
    'Body weight': 'Peso corporal',
    'none (bodyweight exercise)': 'Peso corporal',
    'None (no equipment needed)': 'Sin equipamiento',
    'Kettlebell': 'Kettlebell',
    'Cable': 'Polea',
    'Machine': 'Máquina',
    'Plate': 'Disco',
    'Resistance Band': 'Banda elástica',
    'Resistance band': 'Banda elástica',
    'Bench': 'Banco',
    'Gym mat': 'Colchoneta',
    'Pull-up bar': 'Barra de dominadas',
    'E-Z Curl Bar': 'Barra Z',
    'SZ-Bar': 'Barra Z',
    'Incline bench': 'Banco inclinado',
    'Swiss Ball': 'Pelota suiza',
    'Exercise Ball': 'Pelota suiza',
    'Foam roll': 'Foam roller',
}


def limpiar_html(texto):
    if not texto:
        return ''
    texto = html.unescape(texto)
    texto = re.sub(r'<[^>]+>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


class Command(BaseCommand):
    help = 'Importa ejercicios desde Wger en inglés manteniendo los filtros en español'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Número máximo de ejercicios a importar (útil para pruebas)',
        )

    def handle(self, *args, **options):
        limite = options['limite']

        url = f'{WGER_BASE}/exerciseinfo/?format=json&limit=20'
        creados = 0
        actualizados = 0
        omitidos = 0
        total_procesados = 0

        self.stdout.write(self.style.NOTICE('Iniciando importación directa (Ejercicios en EN / Filtros en ES)...\n'))

        while url:
            if limite and total_procesados >= limite:
                break

            self.stdout.write(f'  Página en curso... ({total_procesados} procesados, '
                              f'{creados} creados, {actualizados} actualizados)')

            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f'Error de conexión: {e}'))
                break

            data = response.json()

            for item in data['results']:
                if limite and total_procesados >= limite:
                    break

                total_procesados += 1

                # 1. Extraer traducciones disponibles
                traducciones = {t['language']: t for t in item.get('translations', [])}
                
                # Prioridad absoluta al Inglés para mantener consistencia original
                traduccion_en = traducciones.get(LANG_EN)
                # Fallback al español o al primer idioma registrado si el inglés no existiera de forma explícita
                traduccion_base = traduccion_en or traducciones.get(LANG_ES) or (item.get('translations', [])[0] if item.get('translations') else None)

                if not traduccion_base or not traduccion_base.get('name', '').strip():
                    omitidos += 1
                    continue

                # Asignamos el nombre y descripción nativos (en inglés si está disponible) sin traducir
                nombre = traduccion_base['name'].strip()
                descripcion = limpiar_html(traduccion_base.get('description', ''))

                # 2. Categoría → Guardamos el filtro mapeado a Español
                cat_en = item.get('category', {}).get('name', '') if item.get('category') else ''
                categoria = CATEGORIAS_ES.get(cat_en, cat_en)

                # 3. Músculo principal → Guardamos el filtro mapeado a Español
                musculos = item.get('muscles', [])
                if musculos:
                    nombre_cientifico = musculos[0].get('name', '')
                    nombre_en_musculo = musculos[0].get('name_en', '')
                    musculo_principal = (
                        MUSCULOS_ES.get(nombre_cientifico)
                        or MUSCULOS_ES.get(nombre_en_musculo)
                        or nombre_en_musculo
                        or nombre_cientifico
                    )
                else:
                    musculo_principal = ''

                # 4. Equipamiento → Guardamos el filtro mapeado a Español
                equipos = item.get('equipment', [])
                equipo_en = equipos[0].get('name', '') if equipos else ''
                equipamiento = EQUIPAMIENTO_ES.get(equipo_en, equipo_en)

                # 5. Imagen
                imagenes = item.get('images', [])
                imagen_url = imagenes[0].get('image', '') if imagenes else ''

                # 6. Guardar o actualizar en la Base de Datos
                _, created = EjercicioCatalogo.objects.update_or_create(
                    wger_id=item['id'],
                    defaults={
                        'nombre': nombre,
                        'descripcion': descripcion,
                        'categoria': categoria,
                        'musculo_principal': musculo_principal,
                        'equipamiento': equipamiento,
                        'imagen_url': imagen_url,
                    },
                )

                if created:
                    creados += 1
                else:
                    actualizados += 1

            url = data.get('next')
            if url:
                # Un pequeño sleep de cortesía para no saturar la API de Wger
                time.sleep(0.1)

        self.stdout.write(self.style.SUCCESS(
            f'\n¡Importación completada con éxito!'
            f'\n  Creados (Nuevos): {creados}'
            f'\n  Actualizados:     {actualizados}'
            f'\n  Omitidos:         {omitidos}'
            f'\n  Total analizados: {total_procesados}'
        ))