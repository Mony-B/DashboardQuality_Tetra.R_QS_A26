from django.conf import settings
from django.db import models
from django.db.models import F, Q

from .metricas import METRICAS, OPCIONES_METRICA


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

    def metricas_en_meta(self):
        """Cuántas de las 5 métricas del periodo actual están en meta (R4).

        Sin medidas capturadas ninguna está en meta (postcondición 4 del CU 01).
        El cálculo real llega con el CU 04, que debe reemplazar este método.
        """
        return 0

    def crear_metas_sugeridas(self):
        MetaProyecto.objects.bulk_create(
            MetaProyecto(proyecto=self, metrica=m.clave, valor=m.meta_sugerida) for m in METRICAS
        )


class Periodo(models.Model):
    """Periodo de trabajo de un proyecto, con nombre libre (R3)."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="periodos")
    nombre = models.CharField("nombre del periodo", max_length=50)
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de fin")

    class Meta:
        ordering = ["fecha_inicio"]
        constraints = [
            models.UniqueConstraint(fields=["proyecto", "nombre"], name="periodo_nombre_unico"),
            models.CheckConstraint(
                condition=Q(fecha_fin__gte=F("fecha_inicio")), name="periodo_fin_no_antes_de_inicio"
            ),
        ]

    def __str__(self):
        return self.nombre

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


class MetaProyecto(models.Model):
    """Meta de una métrica para un proyecto; inicia con la sugerida (R2) y se ajusta en CU 04."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="metas")
    metrica = models.CharField(max_length=30, choices=OPCIONES_METRICA)
    valor = models.PositiveSmallIntegerField("meta (%)")

    class Meta:
        verbose_name = "meta del proyecto"
        verbose_name_plural = "metas del proyecto"
        constraints = [
            models.UniqueConstraint(fields=["proyecto", "metrica"], name="meta_unica_por_metrica"),
        ]

    def __str__(self):
        return f"{self.get_metrica_display()}: {self.valor} %"
