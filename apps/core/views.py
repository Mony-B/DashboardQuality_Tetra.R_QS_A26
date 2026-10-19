from django.views.generic import RedirectView


class InicioView(RedirectView):
    """La pantalla de inicio es Mis proyectos (precondición 2 del CU 01)."""

    pattern_name = "proyectos:mis_proyectos"
