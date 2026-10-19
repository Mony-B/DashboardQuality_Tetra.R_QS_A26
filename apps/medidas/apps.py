from django.apps import AppConfig


class MedidasConfig(AppConfig):
    """CU 02 · Registrar las medidas del periodo (R5, R6, R7).

    Por ahora solo existe la pantalla de destino del CU 01; el CU 02 agrega el formulario.
    """

    name = "apps.medidas"
    label = "medidas"
    verbose_name = "Medidas"
