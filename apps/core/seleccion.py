"""Elegir proyecto y periodo desde la URL (Dashboard y Reportes).

Todo parte de los proyectos del usuario de la sesión: uno ajeno, o un periodo que no
es del proyecto, responde 404 sin revelar que existe (R21).
"""

from django.http import Http404


def entero(valor):
    """Id de la URL como entero; ``None`` si no viene. Un valor no numérico es un 404."""
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except ValueError:
        raise Http404("Identificador inválido") from None


def ubicar(proyectos, proyecto_id, periodo_id):
    """Proyecto y periodo pedidos; por omisión el periodo actual del primer proyecto (paso 1)."""
    if periodo_id is not None:
        for proyecto in proyectos:
            for periodo in proyecto.periodos.all():
                if periodo.pk == periodo_id:
                    if proyecto_id is not None and proyecto.pk != proyecto_id:
                        raise Http404("El periodo no es de ese proyecto")
                    return proyecto, periodo
        raise Http404("Periodo no encontrado")
    if proyecto_id is None:
        proyecto = proyectos[0]
    else:
        proyecto = next((p for p in proyectos if p.pk == proyecto_id), None)
        if proyecto is None:
            raise Http404("Proyecto no encontrado")
    return proyecto, proyecto.periodo_actual
