from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


class Proyecto(models.Model):
    """Proyecto de software que el usuario monitorea (CU 01, R2)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proyectos"
    )
    nombre = models.CharField(max_length=100)
    marco_trabajo = models.CharField("marco de trabajo", max_length=50)
    descripcion = models.CharField("descripción", max_length=500, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "nombre"], name="proyecto_nombre_unico"),
        ]

    def __str__(self):
        return self.nombre

    @property
    def periodo_actual(self):
        """El periodo actual es el de fecha de inicio más reciente."""
        return self.periodos.first()


class Periodo(models.Model):
    """Periodo de trabajo de un proyecto y sus medidas (CU 01 y CU 02, R3 y R5).

    Cada periodo guarda un único conjunto de medidas: al guardar de nuevo se
    reemplaza el anterior. Una medida vacía (``None``) es distinta de 0: la
    métrica que depende de ella queda «sin datos» (CU 04).
    """

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="periodos")
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de fin")

    # M1 · Capacidad funcional
    funciones_requeridas = models.PositiveIntegerField(null=True, blank=True)
    funciones_entregadas = models.PositiveIntegerField(null=True, blank=True)
    # M2 · Tasa de aprobación de pruebas
    casos_ejecutados = models.PositiveIntegerField(null=True, blank=True)
    casos_aprobados = models.PositiveIntegerField(null=True, blank=True)
    # M3 · Cobertura de requisitos por pruebas
    requisitos_verificables = models.PositiveIntegerField(null=True, blank=True)
    requisitos_con_prueba = models.PositiveIntegerField(null=True, blank=True)
    # M4 · Densidad de defectos
    defectos_codigo = models.PositiveIntegerField(null=True, blank=True)
    kloc = models.DecimalField(
        "tamaño del código (KLOC)", max_digits=8, decimal_places=3, null=True, blank=True
    )

    defecto_critico_abierto = models.BooleanField(
        "existe un defecto crítico abierto", default=False
    )

    class Meta:
        ordering = ["-fecha_inicio"]
        constraints = [
            models.UniqueConstraint(fields=["proyecto", "nombre"], name="periodo_nombre_unico"),
            models.CheckConstraint(
                condition=Q(kloc__isnull=True) | Q(kloc__gt=0), name="periodo_kloc_mayor_que_cero"
            ),
        ]

    def __str__(self):
        return self.etiqueta

    @property
    def rango_fechas(self):
        return f"{self.fecha_inicio:%d/%m/%Y} – {self.fecha_fin:%d/%m/%Y}"

    @property
    def etiqueta(self):
        return f"{self.nombre} ({self.rango_fechas})"

    def get_absolute_url_medidas(self):
        return reverse(
            "medidas:captura", kwargs={"proyecto_id": self.proyecto_id, "periodo_id": self.pk}
        )

    def tiene_medidas(self):
        """True si el periodo ya tiene al menos una medida capturada."""
        campos = (
            self.funciones_requeridas,
            self.funciones_entregadas,
            self.casos_ejecutados,
            self.casos_aprobados,
            self.requisitos_verificables,
            self.requisitos_con_prueba,
            self.defectos_codigo,
            self.kloc,
        )
        return any(valor is not None for valor in campos)

    def recalcular_salud(self):
        """Recalcula las métricas, el índice y el estado de salud del periodo (R7).

        Punto de enganche con el CU 04 (app ``tablero``): el CU 02 lo invoca cada
        vez que guarda medidas. Por ahora las métricas se calculan al abrir el
        dashboard, así que no hay nada que persistir; cuando el CU 04 guarde
        resultados del cálculo, se hace aquí.
        """
