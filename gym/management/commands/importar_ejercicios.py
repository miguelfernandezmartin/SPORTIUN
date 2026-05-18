import html
import re
import time

import requests
from django.core.management.base import BaseCommand

from gym.models import EjercicioCatalogo

WGER_BASE = 'https://wger.de/api/v2'
LANG_ES = 4   # Español
LANG_EN = 2   # English

# Traducciones manuales para los campos fijos de la API (no tienen campo ES)
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
    # name_en comunes
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
    texto = html.unescape(texto)
    texto = re.sub(r'<[^>]+>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def traducir(texto, translator):
    """Traduce un texto al español. Devuelve el original si falla."""
    if not texto:
        return ''
    try:
        # Google Translate tiene límite de ~5000 caracteres por petición
        resultado = translator.translate(texto[:4500])
        time.sleep(0.15)  # respetar rate limit
        return resultado or texto
    except Exception:
        return texto


class Command(BaseCommand):
    help = 'Importa ejercicios desde Wger traduciéndolos al español'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Número máximo de ejercicios a importar (útil para pruebas)',
        )
        parser.add_argument(
            '--sin-traducir',
            action='store_true',
            help='Importa en inglés sin traducir (más rápido, para pruebas)',
        )

    def handle(self, *args, **options):
        limite = options['limite']
        sin_traducir = options['sin_traducir']

        translator = None
        if not sin_traducir:
            try:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source='en', target='es')
                self.stdout.write('Traducción automática activada (Google Translate).')
            except ImportError:
                self.stderr.write(self.style.WARNING(
                    'deep-translator no instalado. Ejecuta: pip install deep-translator\n'
                    'Importando sin traducción automática...'
                ))

        url = f'{WGER_BASE}/exerciseinfo/?format=json&limit=20'
        creados = 0
        actualizados = 0
        omitidos = 0
        total_procesados = 0

        self.stdout.write('Iniciando importación desde Wger...\n')

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

                # 1. Obtener traducción: preferimos español de Wger, fallback inglés
                traducciones = {t['language']: t for t in item.get('translations', [])}
                traduccion_es = traducciones.get(LANG_ES)
                traduccion_en = traducciones.get(LANG_EN)
                traduccion_base = traduccion_es or traduccion_en

                if not traduccion_base or not traduccion_base.get('name', '').strip():
                    omitidos += 1
                    continue

                nombre_base = traduccion_base['name'].strip()
                descripcion_base = limpiar_html(traduccion_base.get('description', ''))

                # 2. Si ya hay traducción española en Wger, la usamos directamente
                if traduccion_es:
                    nombre = nombre_base
                    descripcion = descripcion_base
                elif translator:
                    # Traducimos el inglés al español
                    nombre = traducir(nombre_base, translator)
                    descripcion = traducir(descripcion_base[:2000], translator) if descripcion_base else ''
                else:
                    nombre = nombre_base
                    descripcion = descripcion_base

                # 3. Categoría → traducción manual
                cat_en = item.get('category', {}).get('name', '') if item.get('category') else ''
                categoria = CATEGORIAS_ES.get(cat_en, cat_en)

                # 4. Músculo principal → nombre latín → dict ES; si no, name_en → dict ES
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

                # 5. Equipamiento → traducción manual
                equipos = item.get('equipment', [])
                equipo_en = equipos[0].get('name', '') if equipos else ''
                equipamiento = EQUIPAMIENTO_ES.get(equipo_en, equipo_en)

                # 6. Imagen
                imagenes = item.get('images', [])
                imagen_url = imagenes[0].get('image', '') if imagenes else ''

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
                time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS(
            f'\nImportación completada:'
            f'\n  Creados:      {creados}'
            f'\n  Actualizados: {actualizados}'
            f'\n  Omitidos:     {omitidos}'
            f'\n  Total:        {total_procesados}'
        ))
