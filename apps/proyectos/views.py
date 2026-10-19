"""Vistas del CU 01 · Iniciar el monitoreo de un proyecto.

Los nombres siguen el diagrama de secuencia del CU 01. Toda consulta filtra por
``request.user`` para que nadie vea ni modifique proyectos ajenos (R21).
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProyectoPeriodoForm
from .models import Proyecto


def _fecha(valor):
    return valor.strftime("%d/%m/%Y")


def mis_proyectos_view(request):
    """Paso 1: una tarjeta por cada proyecto del usuario (R4)."""
    proyectos = Proyecto.objects.filter(usuario=request.user).prefetch_related("periodos")
    return render(request, "proyectos/mis_proyectos.html", {"proyectos": proyectos})


def nuevo_proyecto_view(request):
    """Pasos 2 a 8: registrar un proyecto con su primer periodo (R2, R3)."""
    form = ProyectoPeriodoForm(request.POST or None, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        periodo = form.save()
        messages.success(
            request,
            f"Proyecto registrado. {periodo.proyecto.nombre} quedó con el periodo "
            f"{periodo.nombre} y las metas sugeridas. Ya puedes capturar sus medidas.",
        )
        return redirect("medidas:captura", pk=periodo.pk)
    return render(request, "proyectos/nuevo_proyecto.html", {"form": form})


def nuevo_periodo_view(request, pk):
    """FA-3: abrir un periodo nuevo en un proyecto existente del usuario."""
    proyecto = get_object_or_404(Proyecto, pk=pk, usuario=request.user)
    form = ProyectoPeriodoForm(request.POST or None, usuario=request.user, proyecto=proyecto)
    if request.method == "POST" and form.is_valid():
        periodo = form.save()
        messages.success(
            request,
            f"Periodo registrado. {periodo.nombre} ({_fecha(periodo.fecha_inicio)} – "
            f"{_fecha(periodo.fecha_fin)}) es ahora el periodo actual de {proyecto.nombre}.",
        )
        return redirect("medidas:captura", pk=periodo.pk)
    return render(
        request,
        "proyectos/nuevo_proyecto.html",
        {"form": form, "proyecto": proyecto, "periodos": proyecto.periodos.all()},
    )
