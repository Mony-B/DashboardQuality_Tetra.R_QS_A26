"""Textos y filas que el Dashboard muestra (CU 04, paso 5). Python puro."""

from . import calculo as c

SEMAFOROS = {c.VERDE: "Verde", c.AMARILLO: "Amarillo", c.ROJO: "Rojo"}


def _valor_con_unidad(definicion, valor):
    texto = c.formatear(valor)
    return f"{texto} %" if definicion.unidad == "%" else texto


def fila_metrica(resultado, medidas):
    """Una métrica lista para la plantilla: valor, color, peso, puntos y motivo o faltante."""
    d = resultado.definicion
    fila = {
        "codigo": d.codigo,
        "nombre": d.nombre,
        "formula": d.formula,
        "peso": d.peso,
        "clave": d.clave,
        "sin_datos": resultado.sin_datos,
        "semaforo": resultado.semaforo or "sin-datos",
        "nombre_semaforo": SEMAFOROS.get(resultado.semaforo, "Sin datos"),
        "unidad_texto": "" if d.unidad == "%" else d.unidad,
        "valor": "" if resultado.sin_datos else _valor_con_unidad(d, resultado.valor),
        "motivo": c.motivo(resultado),
        "faltante": c.medida_faltante(d, medidas) if resultado.sin_datos else "",
        "aporte_texto": "",
    }
    if not resultado.sin_datos:
        fila["aporte_texto"] = (
            f"{resultado.puntos} pts × {d.peso} % = {c.formatear(resultado.aporte)} al índice"
        )
        if d.unidad == "%":
            fila["valor"] = c.formatear(resultado.valor)
            fila["unidad_texto"] = "%"
    return fila


def mensaje_estado(salud):
    """La frase bajo el estado general (pasos 4 y 5; FA-1 y FA-2)."""
    if salud.estado == c.SIN_EVALUAR:
        return (
            "No se calculó el índice: falta información en una o más métricas. "
            "Captura las medidas que faltan en Captura de medidas."
        )
    indice = c.formatear(salud.indice)
    semaforos = [r.semaforo for r in salud.metricas]
    if salud.limitado_por_rojo:
        return (
            f"{c.motivo_r18(salud)} El estado se limita a «En riesgo»; "
            f"se conserva el índice ({indice})."
        )
    if salud.estado == c.SALUDABLE:
        if all(s == c.VERDE for s in semaforos):
            return f"Índice {indice}: las cuatro métricas están en verde."
        return f"Índice {indice}: de 85 a 100. Revisa las métricas que no están en verde."
    rango = "entre 70 y menos de 85" if salud.estado == c.EN_RIESGO else "menor que 70"
    atender = c.ROJO if c.ROJO in semaforos else c.AMARILLO
    sufijo = f" Atiende primero las métricas en {atender}." if atender in semaforos else ""
    return f"Índice {indice}: {rango}.{sufijo}"


def reglas():
    """Tabla de umbrales y pesos (paso 5)."""
    filas = []
    for d in c.DEFINICIONES:
        if d.mayor_es_mejor:
            verde = f"≥ {d.corte_verde:f} %"
            amarillo = f"{d.corte_amarillo:f} – < {d.corte_verde:f} %"
            rojo = f"< {d.corte_amarillo:f} %"
        else:
            verde = f"≤ {d.corte_verde:f}"
            amarillo = f"> {d.corte_verde:f} – {d.corte_amarillo:f}"
            rojo = f"> {d.corte_amarillo:f}"
        filas.append(
            {
                "codigo": d.codigo,
                "nombre": d.nombre,
                "verde": verde,
                "amarillo": amarillo,
                "rojo": rojo,
                "peso": d.peso,
            }
        )
    return filas


def pesos_texto():
    return ", ".join(f"{d.peso} %" for d in c.DEFINICIONES)

