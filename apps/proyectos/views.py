from django.views.generic import ListView

from apps.core.mixins import PropietarioMixin

from .models import Proyecto


class MisProyectosView(PropietarioMixin, ListView):
    """Mis proyectos: una tarjeta por proyecto del usuario.

    Versión mínima: el CU 01 la completa con «+ Nuevo proyecto» y el estado de salud.
    """

    model = Proyecto
    template_name = "proyectos/mis_proyectos.html"
    context_object_name = "proyectos"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["menu_activo"] = "proyectos"
        return contexto

    def get_queryset(self):
        return super().get_queryset().prefetch_related("periodos")
