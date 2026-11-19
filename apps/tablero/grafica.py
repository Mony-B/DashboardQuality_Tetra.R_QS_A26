"""Datos de la gráfica de tendencia (CU 04, paso 7): un punto por periodo.

Python puro. Calcula las coordenadas de un SVG que la plantilla dibuja en el servidor,
así que no hace falta JavaScript. Un periodo sin datos no lleva punto (FA-5): no se
cuenta como 0 ni se une con una línea a sus vecinos.
"""

import math
from decimal import Decimal

from . import calculo as c

ANCHO, ALTO = 420, 210
IZQ, DER, ARRIBA, ABAJO = 62, 22, 18, 46
COLORES = {c.VERDE: "#2e8b4f", c.AMARILLO: "#c18a00", c.ROJO: "#b3261e"}


def _limites(definicion, valores):
    """Mínimo y máximo del eje vertical; siempre incluyen los cortes de la métrica."""
    if definicion.mayor_es_mejor:
        minimo = min([Decimal(60), *valores])
        maximo = max([Decimal(100), *valores])
        return Decimal(math.floor(minimo / 10) * 10), Decimal(math.ceil(maximo / 10) * 10)
    return Decimal(0), Decimal(max(6, math.ceil(max([Decimal(0), *valores])) + 1))


def construir(definicion, periodos):
    """``periodos``: lista de ``(etiqueta, valor o None)`` en orden cronológico."""
    valores = [v for _, v in periodos if v is not None]
    bajo, alto = _limites(definicion, valores)
    ancho_util, alto_util = ANCHO - IZQ - DER, ALTO - ARRIBA - ABAJO

    def y_de(valor):
        return float(ARRIBA + (alto - valor) / (alto - bajo) * alto_util)

    n = len(periodos)
    puntos, segmentos, actual = [], [], []
    for i, (etiqueta, valor) in enumerate(periodos):
        x = IZQ + (ancho_util / 2 if n == 1 else ancho_util * i / (n - 1))
        punto = {"x": round(x, 1), "etiqueta": etiqueta, "sin_datos": valor is None}
        if valor is None:
            if len(actual) > 1:
                segmentos.append(actual)
            actual = []
        else:
            color = c.semaforo(definicion, valor)
            punto.update(
                y=round(y_de(valor), 1),
                y_valor=round(y_de(valor) - 11, 1),
                texto=c.formatear(valor),
                semaforo=color,
                color=COLORES[color],
            )
            actual.append(f"{punto['x']},{punto['y']}")
        puntos.append(punto)
    if len(actual) > 1:
        segmentos.append(actual)

    cortes = sorted({alto, definicion.corte_verde, definicion.corte_amarillo, bajo})
    ejes = [
        {"y": round(y_de(corte), 1), "y_texto": round(y_de(corte) + 3, 1), "texto": f"{corte:f}"}
        for corte in cortes
    ]
    return {
        "ancho": ANCHO,
        "alto": ALTO,
        "izq": IZQ,
        "x_ejes": IZQ - 6,
        "der": ANCHO - DER,
        "y_etiquetas": ALTO - 14,
        "unidad": definicion.unidad,
        "ejes": ejes,
        "puntos": puntos,
        "segmentos": [" ".join(s) for s in segmentos],
        "periodos_sin_datos": [p["etiqueta"] for p in puntos if p["sin_datos"]],
    }
