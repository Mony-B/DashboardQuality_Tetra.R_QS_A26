"""Secciones del reporte y sus textos (CU 05). Python puro, sin ORM."""

from decimal import Decimal

# (clave, texto del formulario). El orden es el del reporte, sin importar cómo se elijan.
SECCIONES = (
    ("resumen", "Resumen de salud (índice y estado general)"),
    ("metricas", "Métricas y su aporte al índice"),
    ("medidas", "Medidas del periodo"),
    ("actividades", "Actividades SQA"),
)
CLAVES = tuple(clave for clave, _ in SECCIONES)

MENSAJE_SIN_SECCION = "Elige al menos una sección."
MENSAJE_SIN_MEDIDAS = (
    "Este periodo no tiene medidas capturadas. "
    "Captúralas en Captura de medidas para generar el reporte."
)
MENSAJE_SIN_ACTIVIDADES = "No hay actividades SQA registradas en este periodo."

ETIQUETAS_MEDIDAS = (
    ("funciones_requeridas", "Funciones requeridas del periodo"),
    ("funciones_entregadas", "Funciones entregadas y aceptadas"),
    ("casos_ejecutados", "Casos de prueba ejecutados"),
    ("casos_aprobados", "Casos de prueba aprobados"),
    ("requisitos_verificables", "Requisitos verificables"),
    ("requisitos_con_prueba", "Requisitos con al menos un caso de prueba"),
    ("defectos_codigo", "Defectos del código detectados"),
    ("kloc", "Tamaño del código (KLOC)"),
)


def elegidas(valores, enviado):
    """Secciones elegidas, en el orden del reporte.

    Sin envío (primera vez que se abre Reportes) vienen las cuatro marcadas. Las claves
    desconocidas se ignoran: solo existen las cuatro secciones del catálogo.
    """
    if not enviado:
        return list(CLAVES)
    pedidas = set(valores)
    return [clave for clave in CLAVES if clave in pedidas]


def _numero(valor):
    if valor is None:
        return "sin dato"
    if isinstance(valor, Decimal):
        texto = f"{valor.normalize():f}"
        return texto if "." in texto else f"{texto}.0"
    return str(valor)


def filas_medidas(medidas):
    """Las ocho medidas guardadas como (etiqueta, valor) para la sección «Medidas»."""
    return [(etiqueta, _numero(getattr(medidas, campo))) for campo, etiqueta in ETIQUETAS_MEDIDAS]


def enlace_seguro(enlace):
    """El enlace de evidencia solo se vuelve vínculo si es http(s); si no, «sin enlace»."""
    enlace = (enlace or "").strip()
    return enlace if enlace.lower().startswith(("http://", "https://")) else ""
