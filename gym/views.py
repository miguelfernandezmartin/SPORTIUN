from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import HttpResponseForbidden
from .models import Rutina, Ejercicio, PerfilUsuario, DiaRutina, EjercicioCatalogo, DIAS_SEMANA, Sesion, EjercicioRegistrado, SerieRegistrada, FeedbackEntrenador
from .forms import EjercicioForm, RutinaForm, PerfilUsuarioForm, DiaRutinaForm
from django.contrib.auth.models import User


@login_required
def rutinas_list(request):
    rutinas = Rutina.objects.filter(usuario=request.user)
    return render(request, 'gym/rutinas_list.html', {'rutinas': rutinas})


@login_required
def crear_rutina(request):
    if request.method == 'POST':
        form = RutinaForm(request.POST)
        if form.is_valid():
            rutina = form.save(commit=False)
            rutina.usuario = request.user
            rutina.save()
            messages.success(request, f'Rutina "{rutina.nombre}" creada correctamente.')
            return redirect('gym:detalle_rutina', rutina_id=rutina.id)
    else:
        form = RutinaForm()
    return render(request, 'gym/crear_rutina.html', {'form': form})


@login_required
def eliminar_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    if request.method == 'POST':
        nombre = rutina.nombre
        rutina.delete()
        messages.success(request, f'Rutina "{nombre}" eliminada correctamente.')
        return redirect('gym:rutinas_list')
    return render(request, 'gym/eliminar_rutina.html', {'rutina': rutina})


@login_required
def detalle_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    dias = rutina.dias.prefetch_related('ejercicios').all()
    return render(request, 'gym/detalle_rutina.html', {'rutina': rutina, 'dias': dias})


@login_required
def crear_dia(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    dias_usados = rutina.dias.values_list('dia', flat=True)

    if request.method == 'POST':
        form = DiaRutinaForm(request.POST)
        if form.is_valid():
            dia = form.save(commit=False)
            dia.rutina = rutina
            try:
                dia.save()
                messages.success(request, f'Día "{dia}" añadido a la rutina.')
                return redirect('gym:detalle_rutina', rutina_id=rutina.id)
            except Exception:
                form.add_error('dia', 'Este día ya está en la rutina.')
    else:
        form = DiaRutinaForm()

    dias_disponibles = [(v, n) for v, n in DIAS_SEMANA if v not in dias_usados]

    if not dias_disponibles:
        messages.info(request, 'Esta rutina ya tiene todos los días de la semana configurados.')
        return redirect('gym:detalle_rutina', rutina_id=rutina.id)

    form.fields['dia'].choices = dias_disponibles
    return render(request, 'gym/crear_dia.html', {'form': form, 'rutina': rutina})


@login_required
def eliminar_dia(request, dia_id):
    dia = get_object_or_404(DiaRutina, id=dia_id)
    if dia.rutina.usuario != request.user:
        messages.error(request, 'No tienes permiso para eliminar este día.')
        return redirect('gym:rutinas_list')

    rutina = dia.rutina
    if request.method == 'POST':
        nombre = str(dia)
        dia.delete()
        messages.success(request, f'Día "{nombre}" eliminado.')
        return redirect('gym:detalle_rutina', rutina_id=rutina.id)

    return render(request, 'gym/eliminar_dia.html', {'dia': dia, 'rutina': rutina})


@login_required
def crear_ejercicio(request, dia_id):
    dia = get_object_or_404(DiaRutina, id=dia_id)
    if dia.rutina.usuario != request.user:
        messages.error(request, 'No tienes permiso para añadir ejercicios aquí.')
        return redirect('gym:rutinas_list')

    if request.method == 'POST':
        form = EjercicioForm(request.POST)
        if form.is_valid():
            ejercicio = form.save(commit=False)
            ejercicio.dia_rutina = dia
            ejercicio.save()
            messages.success(request, f'Ejercicio "{ejercicio.nombre}" añadido.')
            return redirect('gym:detalle_rutina', rutina_id=dia.rutina.id)
    else:
        form = EjercicioForm()

    return render(request, 'gym/crear_ejercicio.html', {'form': form, 'dia': dia, 'rutina': dia.rutina})


@login_required
def eliminar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)

    if not ejercicio.dia_rutina or ejercicio.dia_rutina.rutina.usuario != request.user:
        messages.error(request, 'No tienes permiso para eliminar este ejercicio.')
        return redirect('gym:rutinas_list')

    rutina = ejercicio.dia_rutina.rutina
    if request.method == 'POST':
        nombre = ejercicio.nombre
        ejercicio.delete()
        messages.success(request, f'Ejercicio "{nombre}" eliminado.')
        return redirect('gym:detalle_rutina', rutina_id=rutina.id)

    return render(request, 'gym/eliminar_ejercicio.html', {'ejercicio': ejercicio})


@login_required
def catalogo_ejercicios(request):
    ejercicios = EjercicioCatalogo.objects.all()

    categoria    = request.GET.get('categoria', '')
    musculo      = request.GET.get('musculo', '')
    equipamiento = request.GET.get('equipamiento', '')
    busqueda     = request.GET.get('q', '')
    dia_id       = request.GET.get('dia_id', '')

    if categoria:    ejercicios = ejercicios.filter(categoria=categoria)
    if musculo:      ejercicios = ejercicios.filter(musculo_principal=musculo)
    if equipamiento: ejercicios = ejercicios.filter(equipamiento=equipamiento)
    if busqueda:     ejercicios = ejercicios.filter(nombre__icontains=busqueda)

    categorias = (
        EjercicioCatalogo.objects
        .exclude(categoria='').values_list('categoria', flat=True)
        .distinct().order_by('categoria')
    )
    musculos = (
        EjercicioCatalogo.objects
        .exclude(musculo_principal='').values_list('musculo_principal', flat=True)
        .distinct().order_by('musculo_principal')
    )
    equipamientos = (
        EjercicioCatalogo.objects
        .exclude(equipamiento='').values_list('equipamiento', flat=True)
        .distinct().order_by('equipamiento')
    )

    paginator = Paginator(ejercicios, 24)
    page_obj  = paginator.get_page(request.GET.get('page'))

    dia = None
    if dia_id:
        dia = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    return render(request, 'gym/catalogo.html', {
        'page_obj':     page_obj,
        'categorias':   categorias,
        'musculos':     musculos,
        'equipamientos': equipamientos,
        'dia':          dia,
        'filtros': {
            'categoria':    categoria,
            'musculo':      musculo,
            'equipamiento': equipamiento,
            'q':            busqueda,
            'dia_id':       dia_id,
        },
    })


@login_required
def anadir_desde_catalogo(request, catalogo_id, dia_id):
    item = get_object_or_404(EjercicioCatalogo, id=catalogo_id)
    dia  = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    if request.method == 'POST':
        form = EjercicioForm(request.POST)
        if form.is_valid():
            ejercicio = form.save(commit=False)
            ejercicio.dia_rutina = dia
            ejercicio.save()
            messages.success(request, f'"{ejercicio.nombre}" añadido a {dia}.')
            return redirect('gym:detalle_rutina', rutina_id=dia.rutina.id)
    else:
        form = EjercicioForm(initial={'nombre': item.nombre, 'series': 3, 'repeticiones': 10})

    return render(request, 'gym/anadir_desde_catalogo.html', {
        'form': form, 'item': item, 'dia': dia, 'rutina': dia.rutina,
    })


@login_required
def perfil(request):
    perfil_usuario, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil_usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('gym:perfil')
    else:
        form = PerfilUsuarioForm(instance=perfil_usuario)

    return render(request, 'gym/perfil.html', {'form': form, 'perfil': perfil_usuario})


def es_entrenador(request):
    try:
        p = PerfilUsuario.objects.get(usuario=request.user)
        return p.rol == 'entrenador'
    except PerfilUsuario.DoesNotExist:
        return False


@login_required
def panel_entrenador(request):
    if not es_entrenador(request):
        messages.error(request, 'No tienes permisos para acceder al panel del entrenador.')
        return redirect('gym:rutinas_list')

    clientes = PerfilUsuario.objects.filter(entrenador=request.user, rol='cliente')
    total_clientes       = clientes.count()
    total_sesiones       = Sesion.objects.filter(cliente__perfil__entrenador=request.user).count()
    sesiones_completadas = Sesion.objects.filter(
        cliente__perfil__entrenador=request.user, completada=True
    ).count()

    return render(request, 'gym/panel_entrenador.html', {
        'clientes':            clientes,
        'total_clientes':      total_clientes,
        'total_sesiones':      total_sesiones,
        'sesiones_completadas': sesiones_completadas,
    })


@login_required
def mis_clientes(request):
    if not es_entrenador(request):
        messages.error(request, 'No tienes permisos para ver clientes.')
        return redirect('gym:rutinas_list')

    clientes = PerfilUsuario.objects.filter(entrenador=request.user, rol='cliente')
    busqueda = request.GET.get('q', '')
    if busqueda:
        clientes = clientes.filter(
            Q(usuario__username__icontains=busqueda) |
            Q(usuario__first_name__icontains=busqueda) |
            Q(usuario__email__icontains=busqueda)
        )

    paginator = Paginator(clientes, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'gym/mis_clientes.html', {'page_obj': page_obj, 'busqueda': busqueda})


@login_required
def perfil_cliente(request, cliente_id):
    if not es_entrenador(request):
        messages.error(request, 'No tienes permisos.')
        return redirect('gym:rutinas_list')

    cliente         = get_object_or_404(User, id=cliente_id)
    perfil_cli      = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cli.entrenador != request.user:
        messages.error(request, 'Este cliente no está asignado a ti.')
        return redirect('gym:mis_clientes')

    rutinas              = cliente.rutinas.prefetch_related('dias__ejercicios').all()
    sesiones             = Sesion.objects.filter(cliente=cliente).prefetch_related(
                               'ejercicios_registrados__series',
                               'ejercicios_registrados__ejercicio',
                           ).order_by('-fecha')
    total_sesiones       = sesiones.count()
    sesiones_completadas = sesiones.filter(completada=True).count()
    feedback             = FeedbackEntrenador.objects.filter(cliente=cliente, entrenador=request.user)

    # Peso máximo registrado por el cliente
    peso_max_cliente = (
        SerieRegistrada.objects
        .filter(ejercicio_registrado__sesion__cliente=cliente)
        .aggregate(m=Max('peso'))['m'] or 0
    )

    # Datos gráfica de volumen (últimas 15 sesiones completadas)
    import json
    sesiones_graf = (
        Sesion.objects.filter(cliente=cliente, completada=True)
        .prefetch_related('ejercicios_registrados__series')
        .order_by('fecha')[:15]
    )
    grafica_labels  = []
    grafica_volumen = []
    for s in sesiones_graf:
        vol = sum(
            float(serie.peso or 0) * serie.repeticiones
            for er in s.ejercicios_registrados.all()
            for serie in er.series.all()
        )
        grafica_labels.append(s.fecha.strftime('%d/%m'))
        grafica_volumen.append(round(vol, 1))

    return render(request, 'gym/perfil_cliente.html', {
        'cliente':             cliente,
        'perfil_cliente':      perfil_cli,
        'rutinas':             rutinas,
        'sesiones':            sesiones,
        'total_sesiones':      total_sesiones,
        'sesiones_completadas': sesiones_completadas,
        'feedback':            feedback,
        'peso_max_cliente':    peso_max_cliente,
        'grafica_labels':      json.dumps(grafica_labels),
        'grafica_volumen':     json.dumps(grafica_volumen),
    })


@login_required
def asignar_rutina(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente        = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'No tienes permiso.')
        return redirect('gym:mis_clientes')

    rutinas_entrenador = request.user.rutinas.all()

    if request.method == 'POST':
        rutina_id = request.POST.get('rutina_id')
        rutina    = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)

        nueva_rutina = Rutina.objects.create(
            usuario=cliente,
            nombre=f"{rutina.nombre} (Asignada)",
            descripcion=rutina.descripcion
        )
        for dia in rutina.dias.all():
            nuevo_dia = DiaRutina.objects.create(rutina=nueva_rutina, dia=dia.dia, nombre=dia.nombre)
            for ej in dia.ejercicios.all():
                Ejercicio.objects.create(
                    dia_rutina=nuevo_dia, nombre=ej.nombre,
                    series=ej.series, repeticiones=ej.repeticiones,
                    peso_sugerido=ej.peso_sugerido, descanso=ej.descanso, notas=ej.notas,
                )

        messages.success(request, f'Rutina "{nueva_rutina.nombre}" asignada a {cliente.username}.')
        return redirect('gym:perfil_cliente', cliente_id=cliente.id)

    return render(request, 'gym/asignar_rutina.html', {'cliente': cliente, 'rutinas': rutinas_entrenador})


@login_required
def progreso_cliente(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente        = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'No tienes permiso.')
        return redirect('gym:mis_clientes')

    sesiones  = Sesion.objects.filter(cliente=cliente).order_by('-fecha')
    rutina_id = request.GET.get('rutina_id')
    if rutina_id:
        sesiones = sesiones.filter(rutina_id=rutina_id)

    paginator = Paginator(sesiones, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'gym/progreso_cliente.html', {
        'cliente':   cliente,
        'page_obj':  page_obj,
        'rutinas':   cliente.rutinas.all(),
        'rutina_id': rutina_id,
    })


@login_required
def crear_feedback(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente        = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'No tienes permiso.')
        return redirect('gym:mis_clientes')

    rutinas = cliente.rutinas.all()

    if request.method == 'POST':
        rutina_id = request.POST.get('rutina_id')
        contenido = request.POST.get('contenido')

        if not contenido or not rutina_id:
            messages.error(request, 'Completa todos los campos.')
            return redirect('gym:crear_feedback', cliente_id=cliente.id)

        rutina = get_object_or_404(Rutina, id=rutina_id)
        FeedbackEntrenador.objects.create(
            cliente=cliente, entrenador=request.user, rutina=rutina, contenido=contenido,
        )
        messages.success(request, 'Feedback guardado.')
        return redirect('gym:perfil_cliente', cliente_id=cliente.id)

    return render(request, 'gym/crear_feedback.html', {'cliente': cliente, 'rutinas': rutinas})


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO DE SESIONES (cliente)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def iniciar_sesion(request, dia_id):
    """Inicia una sesión de entrenamiento para un día de rutina."""
    dia = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    from django.utils import timezone
    hoy = timezone.now().date()
    sesion_existente = Sesion.objects.filter(
        cliente=request.user, dia_rutina=dia, completada=False, fecha__date=hoy
    ).first()

    if sesion_existente:
        return redirect('gym:registrar_sesion', sesion_id=sesion_existente.id)

    sesion = Sesion.objects.create(cliente=request.user, rutina=dia.rutina, dia_rutina=dia)
    return redirect('gym:registrar_sesion', sesion_id=sesion.id)


@login_required
def registrar_sesion(request, sesion_id):
    """Formulario para registrar cada serie individualmente por ejercicio."""
    sesion       = get_object_or_404(Sesion, id=sesion_id, cliente=request.user)
    ejercicios_raw = list(sesion.dia_rutina.ejercicios.all())

    # Diccionario ejercicio_id -> EjercicioRegistrado (con sus series prefetchadas)
    registros_previos = {
        r.ejercicio_id: r
        for r in sesion.ejercicios_registrados.prefetch_related('series').all()
    }

    if request.method == 'POST':
        for ej in ejercicios_raw:
            # Obtener o crear el EjercicioRegistrado para este ejercicio en esta sesión
            er, _ = EjercicioRegistrado.objects.get_or_create(sesion=sesion, ejercicio=ej)

            # Borrar series previas y recrearlas con los nuevos valores enviados
            er.series.all().delete()

            for i in range(1, ej.series + 1):
                reps  = request.POST.get(f'reps_{ej.id}_{i}', '').strip()
                peso  = request.POST.get(f'peso_{ej.id}_{i}', '').strip() or None
                notas = request.POST.get(f'notas_serie_{ej.id}_{i}', '').strip()
                if reps:
                    try:
                        SerieRegistrada.objects.create(
                            ejercicio_registrado=er,
                            numero_serie=i,
                            repeticiones=int(reps),
                            peso=float(peso) if peso else None,
                            notas=notas,
                        )
                    except (ValueError, TypeError):
                        pass

        sesion.notas = request.POST.get('notas_sesion', '')
        accion = request.POST.get('accion', 'guardar')
        if accion == 'completar':
            sesion.notas = request.POST.get('notas_sesion', '')
            sesion.completada = True
            sesion.save()
            messages.success(request, f'¡Sesión de {sesion.dia_rutina} completada! 💪')
            return redirect('gym:historial_sesiones')

    # ── GET: preparar datos para el template ─────────────────────────────────
    ejercicios_con_registro = []
    for ej in ejercicios_raw:
        er = registros_previos.get(ej.id)
        # Construir diccionario num_serie -> SerieRegistrada para rellenar valores previos
        series_dict = {s.numero_serie: s for s in er.series.all()} if er else {}

        series_filas = []
        for i in range(1, ej.series + 1):
            s = series_dict.get(i)
            series_filas.append({
                'num':   i,
                'reps':  s.repeticiones if s else '',
                'peso':  s.peso        if s else '',
                'notas': s.notas       if s else '',
            })

        ejercicios_con_registro.append({
            'ejercicio':    ej,
            'series_filas': series_filas,
            'tiene_datos':  bool(er and series_dict),
        })

    return render(request, 'gym/registrar_sesion.html', {
        'sesion':                 sesion,
        'ejercicios_con_registro': ejercicios_con_registro,
    })


@login_required
def historial_sesiones(request):
    """Historial de sesiones del usuario con gráfica de volumen."""
    sesiones  = Sesion.objects.filter(cliente=request.user).select_related(
        'rutina',
        'dia_rutina',
    ).prefetch_related(
        'ejercicios_registrados__series',
        'ejercicios_registrados__ejercicio',
    )
    rutina_id = request.GET.get('rutina_id', '')
    if rutina_id and rutina_id.isdigit():
        sesiones = sesiones.filter(rutina_id=int(rutina_id))
    else:
        rutina_id = ''

    paginator = Paginator(sesiones, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))
    rutinas   = request.user.rutinas.all()

    # Gráfica de volumen (series × reps × peso) por sesión completada
    import json
    qs_grafica = Sesion.objects.filter(cliente=request.user, completada=True)
    if rutina_id:
        qs_grafica = qs_grafica.filter(rutina_id=rutina_id)
    sesiones_graf = qs_grafica.prefetch_related(
        'ejercicios_registrados__series'
    ).order_by('fecha')[:20]

    grafica_labels  = []
    grafica_volumen = []
    for s in sesiones_graf:
        vol = sum(
            float(serie.peso or 0) * serie.repeticiones
            for er in s.ejercicios_registrados.all()
            for serie in er.series.all()
        )
        grafica_labels.append(s.fecha.strftime('%d/%m'))
        grafica_volumen.append(round(vol, 1))

    return render(request, 'gym/historial_sesiones.html', {
        'page_obj':       page_obj,
        'rutinas':        rutinas,
        'rutina_id':      rutina_id,
        'grafica_labels':  json.dumps(grafica_labels),
        'grafica_volumen': json.dumps(grafica_volumen),
    })


@login_required
def mi_progreso(request):
    """Vista de progreso personal con gráficas por ejercicio."""
    import json

    # Ejercicios que el usuario ha registrado alguna vez
    ejercicios_registrados = (
        EjercicioRegistrado.objects
        .filter(sesion__cliente=request.user)
        .values('ejercicio__id', 'ejercicio__nombre')
        .distinct()
        .order_by('ejercicio__nombre')
    )

    ejercicio_sel_id = request.GET.get('ejercicio_id', '')
    grafica_labels   = []
    grafica_peso     = []
    grafica_volumen  = []
    ejercicio_sel    = None

    if ejercicio_sel_id:
        try:
            ejercicio_sel = Ejercicio.objects.get(id=ejercicio_sel_id)
            registros = (
                EjercicioRegistrado.objects
                .filter(sesion__cliente=request.user, ejercicio_id=ejercicio_sel_id)
                .order_by('sesion__fecha')
                .select_related('sesion')
                .prefetch_related('series')
            )
            for er in registros:
                series = list(er.series.all())
                if not series:
                    continue
                # Peso máximo de la sesión y volumen total
                peso_max = max((float(s.peso or 0) for s in series), default=0)
                vol      = sum(float(s.peso or 0) * s.repeticiones for s in series)
                grafica_labels.append(er.sesion.fecha.strftime('%d/%m'))
                grafica_peso.append(peso_max)
                grafica_volumen.append(round(vol, 1))
        except Ejercicio.DoesNotExist:
            pass

    # Stats globales
    total_sesiones       = Sesion.objects.filter(cliente=request.user, completada=True).count()
    total_ejercicios_log = EjercicioRegistrado.objects.filter(sesion__cliente=request.user).count()
    peso_maximo = (
        SerieRegistrada.objects
        .filter(ejercicio_registrado__sesion__cliente=request.user)
        .aggregate(m=Max('peso'))['m'] or 0
    )

    return render(request, 'gym/mi_progreso.html', {
        'ejercicios_registrados': ejercicios_registrados,
        'ejercicio_sel_id':       ejercicio_sel_id,
        'ejercicio_sel':          ejercicio_sel,
        'grafica_labels':         json.dumps(grafica_labels),
        'grafica_peso':           json.dumps(grafica_peso),
        'grafica_volumen':        json.dumps(grafica_volumen),
        'total_sesiones':         total_sesiones,
        'total_ejercicios_log':   total_ejercicios_log,
        'peso_maximo':            peso_maximo,
    })


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT DE ENTRENAMIENTO
# ─────────────────────────────────────────────────────────────────────────────

import json as _json
import urllib.request
import urllib.error

CHATBOT_SYSTEM = """Eres un entrenador personal y experto en fitness dentro de la app Sportiun.
Tu especialidad es el entrenamiento de fuerza, hipertrofia, pérdida de grasa y planificación de rutinas.

Puedes ayudar con:
- Diseñar rutinas semanales (push/pull/legs, full body, torso/pierna, etc.)
- Recomendar ejercicios según objetivos, nivel y equipamiento disponible
- Explicar técnica de ejecución y cómo evitar lesiones
- Orientar sobre series, repeticiones, cargas y descansos
- Principios de sobrecarga progresiva y periodización
- Nutrición básica deportiva (sin reemplazar a un dietista)
- Resolver dudas sobre progreso, estancamientos y recuperación

Responde siempre en español, de forma clara, cercana y motivadora.
Sé concreto: cuando propongas una rutina, da días, ejercicios, series y reps.
Si el usuario no da suficiente información (nivel, objetivo, días disponibles), pregúntale antes de proponer algo.
No respondas preguntas que no tengan relación con el entrenamiento, la salud deportiva o la nutrición."""


def _llamar_api_anthropic(messages_historial):
    """Llama a la API de Anthropic y devuelve el texto de la respuesta."""
    from django.conf import settings as dj_settings
    api_key = getattr(dj_settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY no configurada')

    payload = _json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": CHATBOT_SYSTEM,
        "messages": messages_historial,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST',
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = _json.loads(resp.read().decode('utf-8'))

    return data['content'][0]['text']


@login_required
def chatbot(request):
    """Página principal del chatbot."""
    if 'chatbot_historial' not in request.session:
        request.session['chatbot_historial'] = []
    historial = request.session['chatbot_historial']
    return render(request, 'gym/chatbot.html', {'historial': historial})


@login_required
def chatbot_mensaje(request):
    """Endpoint AJAX: recibe el mensaje del usuario y devuelve la respuesta."""
    if request.method != 'POST':
        from django.http import JsonResponse
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    from django.http import JsonResponse

    try:
        body = _json.loads(request.body)
        mensaje_usuario = body.get('mensaje', '').strip()
    except (_json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    if not mensaje_usuario:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)

    # Recuperar historial de la sesión (máx. 20 turnos para no gastar tokens)
    historial = request.session.get('chatbot_historial', [])
    historial.append({'role': 'user', 'content': mensaje_usuario})
    if len(historial) > 40:
        historial = historial[-40:]

    try:
        respuesta = _llamar_api_anthropic(historial)
    except ValueError:
        return JsonResponse({'error': 'api_key'}, status=200)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        # Si no hay API key configurada, dar mensaje útil en lugar de error crudo
        if e.code in (401, 403):
            return JsonResponse({'error': 'api_key'}, status=200)
        return JsonResponse({'error': f'Error API ({e.code}): {error_body[:200]}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    historial.append({'role': 'assistant', 'content': respuesta})
    request.session['chatbot_historial'] = historial
    request.session.modified = True

    return JsonResponse({'respuesta': respuesta})


@login_required
def chatbot_limpiar(request):
    """Limpia el historial del chatbot."""
    request.session['chatbot_historial'] = []
    request.session.modified = True
    from django.http import JsonResponse
    return JsonResponse({'ok': True})
