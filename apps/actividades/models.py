from django.db import models
from django.urls import reverse

from apps.proyectos.models import Periodo


class Actividad(models.Model):
    """Actividad de aseguramiento de calidad planeada en un periodo (R8, R9).

    Es un registro del proceso, independiente del índice de salud (CU 04). La
    evidencia vive en una carpeta compartida: aquí solo se guarda su enlace (R32).
    """

    class Tecnica(models.TextChoices):
        # Catálogo cerrado de seis técnicas (R8).
        REVISION_PERSONAL = "revision_personal", "Revisión personal"
        REVISION_PARES = "revision_pares", "Revisión entre pares"
        ANALISIS_ESTATICO = "analisis_estatico", "Análisis estático"
        PRUEBA_UNITARIA = "prueba_unitaria", "Prueba unitaria"
        PRUEBA_INTEGRACION = "prueba_integracion", "Prueba de integración"
        PRUEBA_SEGURIDAD = "prueba_seguridad", "Prueba de seguridad"

    class Estado(models.TextChoices):
        PLANEADA = "planeada", "Planeada"
        EN_CURSO = "en_curso", "En curso"
        COMPLETADA = "completada", "Completada"

    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="actividades")
    tecnica = models.CharField("técnica", max_length=30, choices=Tecnica.choices)
    artefacto = models.CharField("artefacto o caso de uso", max_length=120)
    responsable = models.CharField(max_length=80)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PLANEADA)
    enlace_evidencia = models.CharField("enlace a la evidencia", max_length=500, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "actividad SQA"
        verbose_name_plural = "actividades SQA"

    def __str__(self):
        return f"{self.get_tecnica_display()} · {self.artefacto}"

    def get_absolute_url(self):
        return reverse("actividades:lista", kwargs={"periodo_id": self.periodo_id})
