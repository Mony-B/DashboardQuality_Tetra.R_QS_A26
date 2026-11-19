from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.urls import reverse

from apps.tablero.calculo import SIN_EVALUAR, Medidas, evaluar, formatear


class Proyecto(models.Model):
    """Proyecto de software que un usuario monitorea por periodos (R2)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proyectos"
    )
    nombre = models.CharField("nombre del proyecto", max_length=100)
    marco_trabajo = models.CharField("marco de trabajo", max_length=50)
    descripcion = models.TextField("descripción", max_length=500, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            # FA-5: un usuario no repite nombres; usuarios distintos sí pueden.
            models.UniqueConstraint(fields=["usuario", "nombre"], name="proyecto_nombre_unico"),
        ]

    def __str__(self):
        return self.nombre

    @property
    def periodo_actual(self):
        """El periodo con la fecha de inicio más reciente (requisito especial 7)."""
        return self.periodos.order_by("-fecha_inicio").first()

    def resumen_salud(self):
        """Estado de salud del periodo actual para la tarjeta de Mis proyectos (R4)."""
        periodo = self.periodo_actual
        if periodo is None or not periodo.tiene_medidas():
            return {
                "estado": SIN_EVALUAR,
                "nombre": "Sin evaluar",
                "indice": None,
                "detalle": "Sin medidas",
            }
        salud = periodo.salud()
        return {
            "estado": salud.estado,
            "nombre": salud.nombre_estado,
            "indice": formatear(salud.indice) if salud.indice is not None else None,
            "detalle": "Datos incompletos" if salud.estado == SIN_EVALUAR else "",
        }


class Periodo(models.Model):
    """Periodo de trabajo de un proyecto, con nombre libre (R3)."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="periodos")
    nombre = models.CharField("nombre del periodo", max_length=50)
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de fin")

    # Medidas del periodo (CU 02, R5). Un único conjunto por periodo: al guardar de
    # nuevo se reemplaza el anterior. Vacío (None) es distinto de 0: la métrica que
    # depende de esa medida queda «sin datos» (CU 04).
    funciones_requeridas = models.PositiveIntegerField(null=True, blank=True)
    funciones_entregadas = models.PositiveIntegerField(null=True, blank=True)
    casos_ejecutados = models.PositiveIntegerField(null=True, blank=True)
    casos_aprobados = models.PositiveIntegerField(null=True, blank=True)
    requisitos_verificables = models.PositiveIntegerField(null=True, blank=True)
    requisitos_con_prueba = models.PositiveIntegerField(null=True, blank=True)
    defectos_codigo = models.PositiveIntegerField(null=True, blank=True)
    kloc = models.DecimalField(
        "tamaño del código (KLOC)", max_digits=8, decimal_places=3, null=True, blank=True
    )

    class Meta:
        ordering = ["fecha_inicio"]
        constraints = [
            models.UniqueConstraint(fields=["proyecto", "nombre"], name="periodo_nombre_unico"),
            models.CheckConstraint(
                condition=Q(fecha_fin__gte=F("fecha_inicio")), name="periodo_fin_no_antes_de_inicio"
            ),
            models.CheckConstraint(
                condition=Q(kloc__isnull=True) | Q(kloc__gt=0), name="periodo_kloc_mayor_que_cero"
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def etiqueta(self):
        return f"{self.nombre} ({self.fecha_inicio:%d/%m/%Y} – {self.fecha_fin:%d/%m/%Y})"

    def get_absolute_url_medidas(self):
        return reverse(
            "medidas:captura", kwargs={"proyecto_id": self.proyecto_id, "periodo_id": self.pk}
        )

    def get_absolute_url_actividades(self):
        return reverse("actividades:lista", kwargs={"periodo_id": self.pk})

    def tiene_medidas(self):
        """True si el periodo ya tiene al menos una medida capturada."""
        return any(
            valor is not None
            for valor in (
                self.funciones_requeridas,
                self.funciones_entregadas,
                self.casos_ejecutados,
                self.casos_aprobados,
                self.requisitos_verificables,
                self.requisitos_con_prueba,
                self.defectos_codigo,
                self.kloc,
            )
        )

    def salud(self):
        """Métricas, índice y estado de salud del periodo con las medidas guardadas (CU 04)."""
        return evaluar(Medidas.de_periodo(self))

    def recalcular_salud(self):
        """Recalcula la salud del periodo cada vez que se guardan medidas (R7).

        El CU 02 lo invoca al guardar. La salud no se almacena: se calcula a partir de las
        ocho medidas, así el Dashboard y Mis proyectos siempre reflejan lo último guardado.
        """
        return self.salud()

    def traslapes(self):
        """Periodos del mismo proyecto que comparten al menos un día con este (FA-4)."""
        return (
            Periodo.objects.filter(
                proyecto=self.proyecto,
                fecha_inicio__lte=self.fecha_fin,
                fecha_fin__gte=self.fecha_inicio,
            )
            .exclude(pk=self.pk)
            .order_by("fecha_inicio")
        )
