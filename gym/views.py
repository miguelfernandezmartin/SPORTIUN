from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Rutina, Ejercicio, PerfilUsuario, DiaRutina, EjercicioCatalogo, DIAS_SEMANA
from .forms import EjercicioForm, RutinaForm, PerfilUsuarioForm, DiaRutinaForm


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
