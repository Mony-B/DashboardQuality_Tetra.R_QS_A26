"""Vistas del CU 03 · Planear y dar seguimiento a las actividades SQA.

Los nombres siguen el diagrama de secuencia del CU 03. Toda consulta filtra por el
usuario de la sesión: un periodo o una actividad ajenos responden 404 (R21).
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.proyectos.models import Periodo, Proyecto

from .forms import ActividadForm, EnlaceForm, EstadoForm
from .models import Actividad


def _periodo_del_usuario(request, periodo_id):
    return get_object_or_404(
        Periodo.objects.select_related("proyecto"), pk=periodo_id, proyecto__usuario=request.user
    )


def _actividad_del_usuario(request, actividad_id):
    return get_object_or_404(
        Actividad.objects.select_related("periodo__proyecto"),
        pk=actividad_id,
        periodo__proyecto__usuario=request.user,
    )


def _selector(usuario):
    """Proyectos y periodos del usuario para los selectores; cada periodo lleva su dirección."""
    proyectos = Proyecto.objects.filter(usuario=usuario).prefetch_related("periodos")
    return [
        {
            "id": proyecto.pk,
            "nombre": proyecto.nombre,
            "periodos": [
                {
                    "id": p.pk,
                    "etiqueta": p.etiqueta,
                    "url": p.get_absolute_url_actividades(),
                }
                for p in sorted(proyecto.periodos.all(), key=lambda x: x.fecha_inicio, reverse=True)
            ],
        }
        for proyecto in proyectos
    ]


def _pantalla(request, periodo, form=None, error_enlace=None):
    """Formulario "Planear una actividad" y tabla de actividades del periodo."""
    contexto = {
        "periodo": periodo,
        "proyecto": periodo.proyecto,
        "form": form or ActividadForm(),
        "actividades": periodo.actividades.all(),
        "estados": Actividad.Estado.choices,
        # FA-2: (id de la actividad, texto escrito, mensaje) para marcar su fila.
        "error_enlace": error_enlace,
        "selector": _selector(request.user),
    }
    return render(request, "actividades/actividades_sqa.html", contexto)


def inicio_actividades_view(request):
    """Entrada desde el menú «Actividades SQA»: abre el periodo actual de un proyecto."""
    proyecto = Proyecto.objects.filter(usuario=request.user).first()
    periodo = proyecto.periodo_actual if proyecto else None
    if periodo is None:
        messages.info(
            request, "Registra un proyecto con al menos un periodo para planear actividades SQA."
        )
        return redirect("proyectos:mis_proyectos")
    return redirect(periodo.get_absolute_url_actividades())


def actividades_view(request, periodo_id):
    """Pasos 1 y 2: el formulario y la tabla de actividades del periodo (FA-5 si no hay)."""
    return _pantalla(request, _periodo_del_usuario(request, periodo_id))


@require_POST
def planear_actividad_view(request, periodo_id):
    """Pasos 5 a 7: valida los cuatro datos y registra la actividad en estado «planeada»."""
    periodo = _periodo_del_usuario(request, periodo_id)
    form = ActividadForm(request.POST)
    if not form.is_valid():  # FA-1: se conserva lo capturado y se marca cada campo
        return _pantalla(request, periodo, form=form)
    actividad = form.save(commit=False)
    actividad.periodo = periodo
    actividad.save()
    messages.success(request, "Actividad planeada con estado «planeada».")
    return redirect(actividad.get_absolute_url())


@require_POST
def cambiar_estado_view(request, actividad_id):
    """Pasos 8 y 9: guarda el nuevo estado, en cualquier dirección (FA-4); el enlace se conserva."""
    actividad = _actividad_del_usuario(request, actividad_id)
    form = EstadoForm(request.POST)
    if form.is_valid():
        actividad.estado = form.cleaned_data["estado"]
        actividad.save(update_fields=["estado"])
        messages.success(
            request, f"Estado actualizado a «{actividad.get_estado_display().lower()}»."
        )
    else:
        messages.error(request, "Elige un estado válido.")
    return redirect(actividad.get_absolute_url())


@require_POST
def guardar_enlace_view(request, actividad_id):
    """Pasos 10 a 13: guarda, cambia o quita (FA-3) el enlace; uno inválido no se guarda (FA-2)."""
    actividad = _actividad_del_usuario(request, actividad_id)
    form = EnlaceForm(request.POST)
    if not form.is_valid():
        escrito = request.POST.get("enlace", "")
        mensaje = form.errors["enlace"][0]
        return _pantalla(request, actividad.periodo, error_enlace=(actividad.pk, escrito, mensaje))
    enlace = form.cleaned_data["enlace"]
    actividad.enlace_evidencia = enlace
    actividad.save(update_fields=["enlace_evidencia"])
    messages.success(
        request, "Enlace de evidencia guardado." if enlace else "Enlace de evidencia quitado."
    )
    return redirect(actividad.get_absolute_url())
