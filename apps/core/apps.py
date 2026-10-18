from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Piezas compartidas: plantilla base, página de inicio y mixins comunes."""

    name = "apps.core"
    label = "core"
    verbose_name = "Núcleo"
