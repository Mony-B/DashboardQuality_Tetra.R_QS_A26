"""Cálculo de la salud de un periodo (CU 04, R10–R18).

Python puro: no usa el ORM ni Django, así se prueba sin base de datos. Recibe las
ocho medidas del periodo y devuelve las cuatro métricas, el índice y el estado.

Modelo (SRS 1.2): cada métrica da 100, 60 o 0 puntos según su semáforo; el índice es
la suma de puntos × peso. Las actividades SQA (CU 03) no intervienen.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

VERDE, AMARILLO, ROJO = "verde", "amarillo", "rojo"
PUNTOS = {VERDE: 100, AMARILLO: 60, ROJO: 0}

SALUDABLE, EN_RIESGO, CRITICO, SIN_EVALUAR = "saludable", "en_riesgo", "critico", "sin_evaluar"
NOMBRES_ESTADO = {
    SALUDABLE: "Saludable",
    EN_RIESGO: "En riesgo",
    CRITICO: "Crítico",
    SIN_EVALUAR: "Sin evaluar",
}

UMBRAL_SALUDABLE = Decimal("85")
UMBRAL_EN_RIESGO = Decimal("70")


@dataclass(frozen=True)
class DefinicionMetrica:
    clave: str
    nombre: str
    formula: str
    unidad: str
    peso: int  # porcentaje del índice
    # Para métricas donde más es mejor: (verde_desde, amarillo_desde).
    # Para la densidad de defectos (menos es mejor): (verde_hasta, amarillo_hasta).
    corte_verde: Decimal
    corte_amarillo: Decimal
    mayor_es_mejor: bool = True


DEFINICIONES = (
    DefinicionMetrica(
        "capacidad_funcional",
        "Capacidad funcional",
        "Entregadas y aceptadas ÷ requeridas × 100",
        "%",
        25,
        Decimal("95"),
        Decimal("80"),
    ),
    DefinicionMetrica(
        "tasa_aprobacion",
        "Tasa de aprobación de pruebas",
        "Casos aprobados ÷ ejecutados × 100",
        "%",
        30,
        Decimal("95"),
        Decimal("85"),
    ),
    DefinicionMetrica(
        "cobertura_requisitos",
        "Cobertura de requisitos por pruebas",
        "Requisitos con prueba ÷ verificables × 100",
        "%",
        20,
        Decimal("95"),
        Decimal("80"),
    ),
    DefinicionMetrica(
        "densidad_defectos",
        "Densidad de defectos",
        "Defectos del código ÷ KLOC",
        "defectos/KLOC",
        25,
        Decimal("2"),
        Decimal("5"),
        mayor_es_mejor=False,
    ),
)


@dataclass(frozen=True)
class Medidas:
    funciones_requeridas: int | None = None
    funciones_entregadas: int | None = None
    casos_ejecutados: int | None = None
    casos_aprobados: int | None = None
    requisitos_verificables: int | None = None
    requisitos_con_prueba: int | None = None
    defectos_codigo: int | None = None
    kloc: Decimal | None = None

    @classmethod
    def de_periodo(cls, periodo):
        """Toma las ocho medidas de un ``Periodo`` (o cualquier objeto con esos campos)."""
        return cls(**{campo: getattr(periodo, campo) for campo in cls.__dataclass_fields__})


@dataclass(frozen=True)
class ResultadoMetrica:
    definicion: DefinicionMetrica
    valor: Decimal | None  # None = sin datos (R16)
    semaforo: str | None
    puntos: int | None
    aporte: Decimal | None  # puntos × peso, en puntos del índice

    @property
    def clave(self):
        return self.definicion.clave

    @property
    def sin_datos(self):
        return self.valor is None


@dataclass(frozen=True)
class Salud:
    metricas: tuple[ResultadoMetrica, ...]
    indice: Decimal | None
    estado: str
    limitado_por_rojo: bool = False  # R18

    @property
    def nombre_estado(self):
        return NOMBRES_ESTADO[self.estado]


def _razon(numerador, denominador, por=100):
    """numerador ÷ denominador × ``por``; ``None`` si falta un dato o el divisor es 0."""
    if numerador is None or denominador is None or Decimal(denominador) <= 0:
        return None
    return Decimal(numerador) * por / Decimal(denominador)


def valores(medidas):
    """Valor de cada métrica con la fórmula del SRS 1.2; ``None`` si no hay datos."""
    return {
        "capacidad_funcional": _razon(medidas.funciones_entregadas, medidas.funciones_requeridas),
        "tasa_aprobacion": _razon(medidas.casos_aprobados, medidas.casos_ejecutados),
        "cobertura_requisitos": _razon(
            medidas.requisitos_con_prueba, medidas.requisitos_verificables
        ),
        "densidad_defectos": _razon(medidas.defectos_codigo, medidas.kloc, por=1),
    }


def semaforo(definicion, valor):
    """Verde, amarillo o rojo según los cortes de la métrica (R12–R15)."""
    if definicion.mayor_es_mejor:
        if valor >= definicion.corte_verde:
            return VERDE
        return AMARILLO if valor >= definicion.corte_amarillo else ROJO
    if valor <= definicion.corte_verde:
        return VERDE
    return AMARILLO if valor <= definicion.corte_amarillo else ROJO


def estado_por_indice(indice):
    if indice >= UMBRAL_SALUDABLE:
        return SALUDABLE
    return EN_RIESGO if indice >= UMBRAL_EN_RIESGO else CRITICO


def limitar_por_rojo(estado, resultados):
    """R18: «Saludable» con alguna métrica en rojo se limita a «En riesgo»."""
    if estado == SALUDABLE and any(r.semaforo == ROJO for r in resultados):
        return EN_RIESGO
    return estado


def redondear(valor, decimales=1):
    """Redondeo para mostrar (mitad hacia arriba). Los semáforos usan el valor exacto."""
    if valor is None:
        return None
    return valor.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def evaluar(medidas):
    """Calcula las cuatro métricas, el índice y el estado de salud del periodo.

    Si falta alguna métrica (R16) no hay índice y el estado es «Sin evaluar».
    R18: si el índice cae en «Saludable» pero alguna métrica está en rojo, el estado
    se limita a «En riesgo» y el índice se conserva.
    """
    por_clave = valores(medidas)
    resultados = []
    for definicion in DEFINICIONES:
        valor = por_clave[definicion.clave]
        if valor is None:
            resultados.append(ResultadoMetrica(definicion, None, None, None, None))
            continue
        color = semaforo(definicion, valor)
        puntos = PUNTOS[color]
        aporte = Decimal(puntos) * definicion.peso / 100
        resultados.append(ResultadoMetrica(definicion, valor, color, puntos, aporte))

    if any(r.sin_datos for r in resultados):
        return Salud(tuple(resultados), None, SIN_EVALUAR)

    indice = sum((r.aporte for r in resultados), Decimal(0))
    estado = limitar_por_rojo(estado_por_indice(indice), resultados)
    limitado = estado != estado_por_indice(indice)
    return Salud(tuple(resultados), indice, estado, limitado)
