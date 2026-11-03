from django import forms

from apps.proyectos.models import Periodo

MSG_ENTERO = "Escribe un número entero, sin decimales."
MSG_NEGATIVO = "El valor no puede ser negativo."


def _conteo(etiqueta):
    """Campo de conteo: entero mayor o igual a 0 y opcional (una medida vacía no es 0)."""
    return forms.IntegerField(
        label=etiqueta,
        required=False,
        min_value=0,
        error_messages={"invalid": MSG_ENTERO, "min_value": MSG_NEGATIVO},
        widget=forms.NumberInput(attrs={"min": 0, "step": 1, "placeholder": "n"}),
    )


class MedidasPeriodoForm(forms.ModelForm):
    """Las ocho medidas del periodo (R5, R6).

    Con un solo envío se guardan todas las medidas o ninguna. Cualquier medida
    puede quedar vacía; vacía es distinto de 0.
    """

    funciones_requeridas = _conteo("Funciones requeridas del periodo")
    funciones_entregadas = _conteo("Funciones entregadas y aceptadas")
    casos_ejecutados = _conteo("Casos de prueba ejecutados")
    casos_aprobados = _conteo("Casos de prueba aprobados")
    requisitos_verificables = _conteo("Requisitos verificables")
    requisitos_con_prueba = _conteo("Requisitos con al menos un caso de prueba")
    defectos_codigo = _conteo("Defectos del código detectados")
    kloc = forms.DecimalField(
        label="Tamaño del código",
        required=False,
        max_digits=8,
        decimal_places=3,
        error_messages={
            "invalid": "Escribe un número, por ejemplo 2.5.",
            "max_digits": "El KLOC es demasiado grande.",
            "max_decimal_places": "Usa como máximo 3 decimales.",
            "max_whole_digits": "El KLOC es demasiado grande.",
        },
        widget=forms.NumberInput(attrs={"min": 0, "step": "any", "placeholder": "n"}),
    )

    # Cada numerador no puede ser mayor que su total: (numerador, total, mensaje).
    NUMERADORES = (
        (
            "funciones_entregadas",
            "funciones_requeridas",
            "Las funciones entregadas no pueden ser más que las requeridas.",
        ),
        (
            "casos_aprobados",
            "casos_ejecutados",
            "Los casos aprobados no pueden ser más que los ejecutados.",
        ),
        (
            "requisitos_con_prueba",
            "requisitos_verificables",
            "Los requisitos con prueba no pueden ser más que los verificables.",
        ),
    )

    # Los cuatro bloques de métrica: título, fórmula, unidad y campos con su validación.
    BLOQUES = (
        {
            "titulo": "Capacidad funcional",
            "formula": "Funciones entregadas y aceptadas ÷ Funciones requeridas × 100",
            "unidad": "%",
            "campos": (
                ("funciones_requeridas", "Entero ≥ 0"),
                ("funciones_entregadas", "Entero ≥ 0 · no mayor que las requeridas"),
            ),
        },
        {
            "titulo": "Casos de prueba aprobados",
            "formula": "Casos aprobados ÷ Casos ejecutados × 100",
            "unidad": "%",
            "campos": (
                ("casos_ejecutados", "Entero ≥ 0"),
                ("casos_aprobados", "Entero ≥ 0 · no mayor que los ejecutados"),
            ),
        },
        {
            "titulo": "Cobertura de pruebas",
            "formula": "Requisitos con caso de prueba ÷ Requisitos verificables × 100",
            "unidad": "%",
            "campos": (
                ("requisitos_verificables", "Entero ≥ 0"),
                ("requisitos_con_prueba", "Entero ≥ 0 · no mayor que los verificables"),
            ),
        },
        {
            "titulo": "Densidad de defectos",
            "formula": "Defectos del código detectados ÷ Tamaño del código",
            "unidad": "defectos/KLOC",
            "campos": (
                ("defectos_codigo", "Entero ≥ 0"),
                ("kloc", "Decimal > 0 · en KLOC (1 KLOC = 1,000 líneas)"),
            ),
        },
    )

    class Meta:
        model = Periodo
        fields = (
            "funciones_requeridas",
            "funciones_entregadas",
            "casos_ejecutados",
            "casos_aprobados",
            "requisitos_verificables",
            "requisitos_con_prueba",
            "defectos_codigo",
            "kloc",
        )

    def bloques(self):
        """Los bloques listos para la plantilla, con sus campos ya enlazados al formulario."""
        return [
            {
                **bloque,
                "campos": [(self[nombre], ayuda) for nombre, ayuda in bloque["campos"]],
            }
            for bloque in self.BLOQUES
        ]

    def clean_kloc(self):
        kloc = self.cleaned_data.get("kloc")
        if kloc is not None and kloc <= 0:
            raise forms.ValidationError("El KLOC debe ser mayor que 0.")
        return kloc

    def clean(self):
        datos = super().clean()
        for numerador, total, mensaje in self.NUMERADORES:
            valor, limite = datos.get(numerador), datos.get(total)
            if valor is not None and limite is not None and valor > limite:
                self.add_error(numerador, mensaje)
        return datos
