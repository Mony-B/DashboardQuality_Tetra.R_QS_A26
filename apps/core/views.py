from django.views.generic import TemplateView


class InicioView(TemplateView):
    """Pantalla de inicio tras iniciar sesión.

    Provisional: cuando exista la app de proyectos (CU 01), esta ruta
    redirigirá a Mis proyectos.
    """

    template_name = "core/inicio.html"
