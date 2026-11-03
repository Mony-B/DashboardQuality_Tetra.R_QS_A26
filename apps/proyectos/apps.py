from django.apps import AppConfig


class ProyectosConfig(AppConfig):
    """Proyectos y periodos (CU 01). Aquí viven también las medidas de cada periodo (CU 02)."""

    name = "apps.proyectos"
    label = "proyectos"
    verbose_name = "Proyectos"
