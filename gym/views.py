from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models as db_models
from django.http import HttpResponseForbidden
from .models import Rutina, Ejercicio, PerfilUsuario, DiaRutina, EjercicioCatalogo, DIAS_SEMANA, Sesion, EjercicioRegistrado, FeedbackEntrenador
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

    # Excluir días ya usados de las opciones del formulario
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

    # Parámetros de filtro
    categoria = request.GET.get('categoria', '')
    musculo = request.GET.get('musculo', '')
    equipamiento = request.GET.get('equipamiento', '')
    busqueda = request.GET.get('q', '')
    dia_id = request.GET.get('dia_id', '')

    if categoria:
        ejercicios = ejercicios.filter(categoria=categoria)
    if musculo:
        ejercicios = ejercicios.filter(musculo_principal=musculo)
    if equipamiento:
        ejercicios = ejercicios.filter(equipamiento=equipamiento)
    if busqueda:
        ejercicios = ejercicios.filter(nombre__icontains=busqueda)

    # Opciones para los desplegables de filtro
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
    page_obj = paginator.get_page(request.GET.get('page'))

    dia = None
    if dia_id:
        dia = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    return render(request, 'gym/catalogo.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'musculos': musculos,
        'equipamientos': equipamientos,
        'dia': dia,
        'filtros': {
            'categoria': categoria,
            'musculo': musculo,
            'equipamiento': equipamiento,
            'q': busqueda,
            'dia_id': dia_id,
        },
    })


@login_required
def anadir_desde_catalogo(request, catalogo_id, dia_id):
    item = get_object_or_404(EjercicioCatalogo, id=catalogo_id)
    dia = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    if request.method == 'POST':
        form = EjercicioForm(request.POST)
        if form.is_valid():
            ejercicio = form.save(commit=False)
            ejercicio.dia_rutina = dia
            ejercicio.save()
            messages.success(request, f'"{ejercicio.nombre}" añadido a {dia}.')
            return redirect('gym:detalle_rutina', rutina_id=dia.rutina.id)
    else:
        form = EjercicioForm(initial={
            'nombre': item.nombre,
            'series': 3,
            'repeticiones': 10,
        })

    return render(request, 'gym/anadir_desde_catalogo.html', {
        'form': form,
        'item': item,
        'dia': dia,
        'rutina': dia.rutina,
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
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        return perfil.rol == 'entrenador'
    except PerfilUsuario.DoesNotExist:
        return False


@login_required
def panel_entrenador(request):
    if not es_entrenador(request):
        messages.error(request, 'No tienes permisos para acceder al panel del entrenador.')
        return redirect('gym:rutinas_list')

    perfil = PerfilUsuario.objects.get(usuario=request.user)
    clientes = PerfilUsuario.objects.filter(entrenador=request.user, rol='cliente')

    total_clientes = clientes.count()
    total_sesiones = Sesion.objects.filter(cliente__perfil__entrenador=request.user).count()
    sesiones_completadas = Sesion.objects.filter(
        cliente__perfil__entrenador=request.user,
        completada=True
    ).count()

    context = {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'total_sesiones': total_sesiones,
        'sesiones_completadas': sesiones_completadas,
    }
    return render(request, 'gym/panel_entrenador.html', context)


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
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'gym/mis_clientes.html', {
        'page_obj': page_obj,
        'busqueda': busqueda
    })


@login_required
def perfil_cliente(request, cliente_id):
    if not es_entrenador(request):
        messages.error(request, 'No tienes permisos.')
        return redirect('gym:rutinas_list')

    cliente = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'Este cliente no está asignado a ti.')
        return redirect('gym:mis_clientes')

    rutinas = cliente.rutinas.all()
    sesiones_recientes = Sesion.objects.filter(cliente=cliente).order_by('-fecha')[:5]
    feedback = FeedbackEntrenador.objects.filter(cliente=cliente, entrenador=request.user)

    context = {
        'cliente': cliente,
        'perfil_cliente': perfil_cliente,
        'rutinas': rutinas,
        'sesiones_recientes': sesiones_recientes,
        'feedback': feedback,
    }
    return render(request, 'gym/perfil_cliente.html', context)


@login_required
def asignar_rutina(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'No tienes permiso.')
        return redirect('gym:mis_clientes')

    rutinas_entrenador = request.user.rutinas.all()

    if request.method == 'POST':
        rutina_id = request.POST.get('rutina_id')
        rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)

        nueva_rutina = Rutina.objects.create(
            usuario=cliente,
            nombre=f"{rutina.nombre} (Asignada)",
            descripcion=rutina.descripcion
        )

        for dia in rutina.dias.all():
            nuevo_dia = DiaRutina.objects.create(
                rutina=nueva_rutina,
                dia=dia.dia,
                nombre=dia.nombre
            )

            for ejercicio in dia.ejercicios.all():
                Ejercicio.objects.create(
                    dia_rutina=nuevo_dia,
                    nombre=ejercicio.nombre,
                    series=ejercicio.series,
                    repeticiones=ejercicio.repeticiones,
                    peso_sugerido=ejercicio.peso_sugerido,
                    descanso=ejercicio.descanso,
                    notas=ejercicio.notas,
                )

        messages.success(request, f'Rutina "{nueva_rutina.nombre}" asignada a {cliente.username}.')
        return redirect('gym:perfil_cliente', cliente_id=cliente.id)

    return render(request, 'gym/asignar_rutina.html', {
        'cliente': cliente,
        'rutinas': rutinas_entrenador,
    })


@login_required
def progreso_cliente(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente = get_object_or_404(User, id=cliente_id)
    perfil_cliente = get_object_or_404(PerfilUsuario, usuario=cliente)

    if perfil_cliente.entrenador != request.user:
        messages.error(request, 'No tienes permiso.')
        return redirect('gym:mis_clientes')

    sesiones = Sesion.objects.filter(cliente=cliente).order_by('-fecha')
    rutina_id = request.GET.get('rutina_id')

    if rutina_id:
        sesiones = sesiones.filter(rutina_id=rutina_id)

    paginator = Paginator(sesiones, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    rutinas_cliente = cliente.rutinas.all()

    context = {
        'cliente': cliente,
        'page_obj': page_obj,
        'rutinas': rutinas_cliente,
        'rutina_id': rutina_id,
    }
    return render(request, 'gym/progreso_cliente.html', context)


@login_required
def crear_feedback(request, cliente_id):
    if not es_entrenador(request):
        return HttpResponseForbidden()

    cliente = get_object_or_404(User, id=cliente_id)
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
            cliente=cliente,
            entrenador=request.user,
            rutina=rutina,
            contenido=contenido,
        )

        messages.success(request, 'Feedback guardado.')
        return redirect('gym:perfil_cliente', cliente_id=cliente.id)

    return render(request, 'gym/crear_feedback.html', {
        'cliente': cliente,
        'rutinas': rutinas,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO DE SESIONES (cliente)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def iniciar_sesion(request, dia_id):
    """Inicia una sesión de entrenamiento para un día de rutina."""
    dia = get_object_or_404(DiaRutina, id=dia_id, rutina__usuario=request.user)

    # Si ya hay una sesión incompleta del día de hoy, redirigir a ella
    from django.utils import timezone
    hoy = timezone.now().date()
    sesion_existente = Sesion.objects.filter(
        cliente=request.user,
        dia_rutina=dia,
        completada=False,
        fecha__date=hoy
    ).first()

    if sesion_existente:
        return redirect('gym:registrar_sesion', sesion_id=sesion_existente.id)

    sesion = Sesion.objects.create(
        cliente=request.user,
        rutina=dia.rutina,
        dia_rutina=dia,
    )
    return redirect('gym:registrar_sesion', sesion_id=sesion.id)


@login_required
def registrar_sesion(request, sesion_id):
    """Formulario para registrar los ejercicios completados en una sesión."""
    sesion = get_object_or_404(Sesion, id=sesion_id, cliente=request.user)
    ejercicios_raw = list(sesion.dia_rutina.ejercicios.all())
    registros_previos = {r.ejercicio_id: r for r in sesion.ejercicios_registrados.all()}

    if request.method == 'POST':
        for ejercicio in ejercicios_raw:
            er, _ = EjercicioRegistrado.objects.get_or_create(
                sesion=sesion,
                ejercicio=ejercicio,
                defaults={
                    'series_completadas': 0,
                    'repeticiones_realizadas': 0,
                }
            )
            
            # Borra las series previas y las vuelve a crear con los nuevos valores
            er.series.all().delete()
            num_series = ejercicio.series  # cuántas filas de serie hay en el form
            
            for i in range(1, num_series + 1):
                reps = request.POST.get(f'reps_{ejercicio.id}_{i}', '').strip()
                peso = request.POST.get(f'peso_{ejercicio.id}_{i}', '').strip() or None
                notas = request.POST.get(f'notas_serie_{ejercicio.id}_{i}', '').strip()
                
                if reps:
                    SerieRegistrada.objects.create(
                        ejercicio_registrado=er,
                        numero_serie=i,
                        repeticiones=int(reps),
                        peso=float(peso) if peso else None,
                        notas=notas,
                    )

        sesion.notas = request.POST.get('notas_sesion', '')
        accion = request.POST.get('accion', 'guardar')
        
        if accion == 'completar':
            sesion.completada = True
            sesion.save()
            messages.success(request, f'¡Sesión de {sesion.dia_rutina} completada! 💪')
            return redirect('gym:historial_sesiones')
        else:
            sesion.save()
            messages.success(request, 'Progreso guardado.')
            return redirect('gym:registrar_sesion', sesion_id=sesion.id)

    # Preparar el contexto para el GET
    ejercicios_con_registro = []
    for ej in ejercicios_raw:
        er = registros_previos.get(ej.id)
        series_previas = list(er.series.all()) if er else []
        series_dict = {s.numero_serie: s for s in series_previas}
        
        series_filas = []
        for i in range(1, ej.series + 1):
            s = series_dict.get(i)
            series_filas.append({
                'num':   i,
                'reps':  s.repeticiones if s else '',
                'peso':  s.peso if s else '',
                'notas': s.notas if s else '',
            })
            
        ejercicios_con_registro.append({
            'ejercicio':    ej,
            'previo':       er,
            'series_filas': series_filas,
        })

    return render(request, 'gym/registrar_sesion.html', {
        'sesion':    sesion,
        'ejercicios_con_registro': ejercicios_con_registro,
    })


@login_required
def historial_sesiones(request):
    """Historial de sesiones del usuario con gráficas de progreso."""
    sesiones = Sesion.objects.filter(cliente=request.user).prefetch_related(
        'ejercicios_registrados__ejercicio'
    )

    rutina_id = request.GET.get('rutina_id', '')
    if rutina_id:
        sesiones = sesiones.filter(rutina_id=rutina_id)

    paginator = Paginator(sesiones, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    rutinas = request.user.rutinas.all()

    # Datos para gráficas: volumen por sesión (últimas 10 completadas)
    import json
    sesiones_completadas = Sesion.objects.filter(
        cliente=request.user, completada=True
    ).prefetch_related('ejercicios_registrados').order_by('fecha')[:20]

    grafica_labels = []
    grafica_volumen = []
    for s in sesiones_completadas:
        vol = sum(
            (r.series_completadas * r.repeticiones_realizadas * float(r.peso_utilizado or 0))
            for r in s.ejercicios_registrados.all()
        )
        grafica_labels.append(s.fecha.strftime('%d/%m'))
        grafica_volumen.append(round(vol, 1))

    return render(request, 'gym/historial_sesiones.html', {
        'page_obj': page_obj,
        'rutinas': rutinas,
        'rutina_id': rutina_id,
        'grafica_labels': json.dumps(grafica_labels),
        'grafica_volumen': json.dumps(grafica_volumen),
    })


@login_required
def mi_progreso(request):
    """Vista de progreso personal con gráficas por ejercicio."""
    import json
    from django.db.models import Avg

    # Ejercicios que el usuario ha registrado alguna vez
    ejercicios_registrados = (
        EjercicioRegistrado.objects
        .filter(sesion__cliente=request.user)
        .values('ejercicio__id', 'ejercicio__nombre')
        .distinct()
        .order_by('ejercicio__nombre')
    )

    ejercicio_sel_id = request.GET.get('ejercicio_id', '')
    grafica_labels = []
    grafica_peso = []
    grafica_volumen = []
    ejercicio_sel = None

    if ejercicio_sel_id:
        try:
            ejercicio_sel = Ejercicio.objects.get(id=ejercicio_sel_id)
            registros = (
                EjercicioRegistrado.objects
                .filter(sesion__cliente=request.user, ejercicio_id=ejercicio_sel_id)
                .order_by('sesion__fecha')
                .select_related('sesion')
            )
            for r in registros:
                grafica_labels.append(r.sesion.fecha.strftime('%d/%m'))
                grafica_peso.append(float(r.peso_utilizado or 0))
                grafica_volumen.append(
                    round(r.series_completadas * r.repeticiones_realizadas * float(r.peso_utilizado or 0), 1)
                )
        except Ejercicio.DoesNotExist:
            pass

    # Stats globales
    total_sesiones = Sesion.objects.filter(cliente=request.user, completada=True).count()
    total_ejercicios_log = EjercicioRegistrado.objects.filter(sesion__cliente=request.user).count()
    peso_maximo = (
        EjercicioRegistrado.objects
        .filter(sesion__cliente=request.user)
        .aggregate(m=db_models.Max('peso_utilizado'))['m'] or 0
    )

    return render(request, 'gym/mi_progreso.html', {
        'ejercicios_registrados': ejercicios_registrados,
        'ejercicio_sel_id': ejercicio_sel_id,
        'ejercicio_sel': ejercicio_sel,
        'grafica_labels': json.dumps(grafica_labels),
        'grafica_peso': json.dumps(grafica_peso),
        'grafica_volumen': json.dumps(grafica_volumen),
        'total_sesiones': total_sesiones,
        'total_ejercicios_log': total_ejercicios_log,
        'peso_maximo': peso_maximo,
    })
