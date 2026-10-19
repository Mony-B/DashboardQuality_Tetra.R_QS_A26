"""Catálogo de las 5 métricas de calidad (Estrategia de Aseguramiento de Calidad, sección 4).

Es la única fuente de las claves, metas sugeridas y mínimos. Lo usan el CU 01 (metas
iniciales de cada proyecto) y lo usarán el CU 02 (medidas) y el CU 04 (cálculo y ajuste).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metrica:
    clave: str
    nombre: str
    factor: str
    criterio: str
    meta_sugerida: int  # porcentaje
    minimo: int  # porcentaje; la meta ajustada no puede bajar de aquí (R18)


METRICAS = (
    Metrica(
        "capacidad_funcional",
        "Capacidad funcional",
        "Functional Suitability",
        "Functional completeness",
        meta_sugerida=100,
        minimo=80,
    ),
    Metrica(
        "casos_aprobados",
        "Casos de prueba aprobados",
        "Functional Suitability",
        "Functional correctness",
        meta_sugerida=95,
        minimo=90,
    ),
    Metrica(
        "pertinencia_funcional",
        "Pertinencia funcional",
        "Functional Suitability",
        "Functional appropriateness",
        meta_sugerida=100,
        minimo=80,
    ),
    Metrica(
        "cobertura_pruebas",
        "Cobertura de pruebas",
        "Reliability",
        "Maturity",
        meta_sugerida=100,
        minimo=90,
    ),
    Metrica(
        "validacion_entradas",
        "Validación de entradas",
        "Security",
        "Integrity",
        meta_sugerida=100,
        minimo=100,
    ),
)

OPCIONES_METRICA = [(m.clave, m.nombre) for m in METRICAS]
