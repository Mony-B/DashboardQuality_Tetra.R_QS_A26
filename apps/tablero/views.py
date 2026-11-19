"""Vistas del CU 04 · Evaluar la salud del proyecto en un periodo.

Solo lectura: consultar el Dashboard no modifica medidas ni actividades. Toda consulta
parte de los proyectos del usuario de la sesión, así que un proyecto o periodo ajeno
responde 404 (R21).
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.core.seleccion import entero, ubicar
from apps.proyectos.models import Proyecto

from . import calculo as c
from . import grafica, presentacion


@require_GET
def dashboard_salud_view(request):
    """Pasos 1 a 7 y FA-1 a FA-5: índice, estado, cuatro métricas y tendencia de una métrica."""
    proyectos = list(Proyecto.objects.filter(usuario=request.user).prefetch_related("periodos"))
    proyecto_id = entero(request.GET.get("proyecto"))
    periodo_id = entero(request.GET.get("periodo"))
    if not proyectos:
        messages.info(request, "Registra un proyecto con al menos un periodo para ver su salud.")
        return redirect("proyectos:mis_proyectos")
    proyecto, periodo = ubicar(proyectos, proyecto_id, periodo_id)
    if periodo is None:
        messages.info(request, "Este proyecto todavía no tiene periodos.")
        return redirect("proyectos:mis_proyectos")

    medidas = c.Medidas.de_periodo(periodo)
    salud = c.evaluar(medidas)
    metricas = [presentacion.fila_metrica(r, medidas) for r in salud.metricas]

    clave = request.GET.get("metrica")
    definicion = next((d for d in c.DEFINICIONES if d.clave == clave), c.DEFINICIONES[0])
    periodos = sorted(proyecto.periodos.all(), key=lambda p: p.fecha_inicio)
    puntos = [
        (p.nombre, c.valores(c.Medidas.de_periodo(p))[definicion.clave]) for p in periodos
    ]
    tendencia = grafica.construir(definicion, puntos)

    contexto = {
        "proyecto": proyecto,
        "periodo": periodo,
        "proyectos": proyectos,
        "periodos": sorted(proyecto.periodos.all(), key=lambda p: p.fecha_inicio, reverse=True),
        "salud": salud,
        "indice": c.formatear(salud.indice) if salud.indice is not None else None,
        "mensaje_estado": presentacion.mensaje_estado(salud),
        "metricas": metricas,
        "definiciones": c.DEFINICIONES,
        "definicion": definicion,
        "tendencia": tendencia,
        "un_solo_periodo": len(periodos) == 1,
        "reglas": presentacion.reglas(),
        "pesos": presentacion.pesos_texto(),
    }
    return render(request, "tablero/dashboard_salud.html", contexto)
