from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import UpdateView

from apps.core.mixins import PropietarioMixin
from apps.proyectos.models import Periodo, Proyecto

from .forms import MedidasPeriodoForm

MENSAJE_GUARDADO = (
    "Medidas guardadas. El sistema solicitó el recálculo de las métricas, "
    "el índice y el estado de salud del periodo (CU 04)."
)


class CapturaMedidasView(PropietarioMixin, UpdateView):
    """Captura de medidas de un periodo (CU 02).

    GET  /proyectos/<id>/periodos/<id>/medidas/ muestra las medidas guardadas (o vacías).
    POST valida con MedidasPeriodoForm, guarda las ocho medidas en una sola operación
    (reemplazan al conjunto anterior), recalcula la salud del periodo (R7) y vuelve a
    mostrar la pantalla con «Medidas guardadas». Un periodo ajeno responde 404 (R21).
    """

    model = Periodo
    form_class = MedidasPeriodoForm
    template_name = "medidas/captura_medidas.html"
    pk_url_kwarg = "periodo_id"
    campo_propietario = "proyecto__usuario"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(proyecto_id=self.kwargs["proyecto_id"])
            .select_related("proyecto")
        )

    def get_object(self, queryset=None):
        periodo = super().get_object(queryset)
        # Se guarda antes de que el formulario toque la instancia al validar.
        self.tenia_medidas = periodo.tiene_medidas()
        return periodo

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            self.object.recalcular_salud()
        messages.success(self.request, MENSAJE_GUARDADO)
        return redirect(self.object.get_absolute_url_medidas())

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        periodo = self.object
        proyectos = (
            Proyecto.objects.filter(usuario=self.request.user)
            .prefetch_related("periodos")
            .order_by("nombre")
        )
        # Para los selectores de Proyecto y Periodo: cada periodo lleva su dirección.
        selector = [
            {
                "id": proyecto.pk,
                "nombre": proyecto.nombre,
                "periodos": [
                    {
                        "id": p.pk,
                        "etiqueta": p.etiqueta,
                        "url": p.get_absolute_url_medidas(),
                    }
                    for p in proyecto.periodos.all()
                ],
            }
            for proyecto in proyectos
        ]
        contexto.update(
            menu_activo="medidas",
            proyecto=periodo.proyecto,
            periodo=periodo,
            bloques=contexto["form"].bloques(),
            tenia_medidas=self.tenia_medidas,
            recien_guardado=any(
                mensaje.level == messages.SUCCESS for mensaje in messages.get_messages(self.request)
            ),
            selector=selector,
            url_mis_proyectos=reverse("proyectos:mis_proyectos"),
        )
        return contexto


class InicioCapturaView(View):
    """Entrada desde el menú «Captura de medidas»: abre el periodo actual de un proyecto."""

    def get(self, request):
        proyecto = (
            Proyecto.objects.filter(usuario=request.user).prefetch_related("periodos").first()
        )
        periodo = proyecto.periodo_actual if proyecto else None
        if periodo is None:
            messages.info(
                request, "Registra un proyecto con al menos un periodo para capturar sus medidas."
            )
            return redirect("proyectos:mis_proyectos")
        return redirect(periodo.get_absolute_url_medidas())
