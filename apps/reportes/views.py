"""Vista del CU 05 · Generar el reporte de salud de un periodo.

Una sola pantalla: sin ``generar`` en la URL muestra el formulario; con ``generar`` valida
y, si todo está bien, muestra el reporte en el navegador. El reporte no se guarda ni se
exporta (se imprime con el navegador) y la consulta es de solo lectura. Toda consulta
parte de los proyectos del usuario: uno ajeno responde 404 (R21).
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.core.seleccion import entero, ubicar
from apps.proyectos.models import Proyecto
from apps.tablero import calculo as c
from apps.tablero import presentacion

from . import secciones as s


def _formulario(request, proyectos, proyecto, periodo, marcadas, errores):
    contexto = {
        "proyectos": proyectos,
        "proyecto": proyecto,
        "periodo": periodo,
        "periodos": sorted(proyecto.periodos.all(), key=lambda p: p.fecha_inicio, reverse=True),
        "secciones": [(clave, texto, clave in marcadas) for clave, texto in s.SECCIONES],
        "error_secciones": errores.get("secciones", ""),
        "sin_medidas": errores.get("sin_medidas", False),
        "mensaje_sin_medidas": s.MENSAJE_SIN_MEDIDAS,
    }
    return render(request, "reportes/formulario.html", contexto)


def _consulta_formulario(proyecto, periodo, marcadas):
    """Dirección para volver al formulario con lo mismo elegido (FA-5)."""
    partes = [f"proyecto={proyecto.pk}", f"periodo={periodo.pk}", "enviado=1"]
    partes += [f"secciones={clave}" for clave in marcadas]
    return "?" + "&".join(partes)


def _reporte(request, proyecto, periodo, marcadas):
    medidas = c.Medidas.de_periodo(periodo)
    salud = c.evaluar(medidas)
    actividades = [
        {
            "tecnica": a.get_tecnica_display(),
            "artefacto": a.artefacto,
            "responsable": a.responsable,
            "estado": a.get_estado_display(),
            "enlace": s.enlace_seguro(a.enlace_evidencia),
        }
        for a in periodo.actividades.all()
    ]
    contexto = {
        "proyecto": proyecto,
        "periodo": periodo,
        "generado_el": timezone.localdate(),
        "generado_por": request.user.get_username(),
        "marcadas": marcadas,
        "salud": salud,
        "indice": c.formatear(salud.indice) if salud.indice is not None else None,
        "metricas": [presentacion.fila_metrica(r, medidas) for r in salud.metricas],
        "medidas": s.filas_medidas(medidas),
        "actividades": actividades,
        "mensaje_sin_actividades": s.MENSAJE_SIN_ACTIVIDADES,
        "volver": _consulta_formulario(proyecto, periodo, marcadas),
    }
    return render(request, "reportes/reporte_salud.html", contexto)


@require_GET
def reportes_view(request):
    """Pasos 1 a 8 y FA-1 a FA-5."""
    proyectos = list(Proyecto.objects.filter(usuario=request.user).prefetch_related("periodos"))
    if not proyectos:
        messages.info(
            request, "Registra un proyecto con al menos un periodo para generar reportes."
        )
        return redirect("proyectos:mis_proyectos")
    try:
        proyecto, periodo = ubicar(
            proyectos, entero(request.GET.get("proyecto")), entero(request.GET.get("periodo"))
        )
    except Http404:  # FE-2: ajeno, inexistente o mal formado; no se muestra ningún dato
        return render(request, "reportes/no_encontrado.html", status=404)
    if periodo is None:
        messages.info(request, "Este proyecto todavía no tiene periodos.")
        return redirect("proyectos:mis_proyectos")

    generar = "generar" in request.GET
    enviado = generar or "enviado" in request.GET
    marcadas = s.elegidas(request.GET.getlist("secciones"), enviado)
    if not generar:
        return _formulario(request, proyectos, proyecto, periodo, marcadas, {})

    errores = {}
    if not marcadas:  # FA-2
        errores["secciones"] = s.MENSAJE_SIN_SECCION
    if not periodo.tiene_medidas():  # FA-1
        errores["sin_medidas"] = True
    if errores:
        return _formulario(request, proyectos, proyecto, periodo, marcadas, errores)
    return _reporte(request, proyecto, periodo, marcadas)
