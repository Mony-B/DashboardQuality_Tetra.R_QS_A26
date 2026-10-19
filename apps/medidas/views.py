from django.shortcuts import get_object_or_404, render

from apps.proyectos.metricas import METRICAS
from apps.proyectos.models import Periodo


def captura_medidas_view(request, pk):
    """Captura de medidas del periodo (CU 02).

    PROVISIONAL: solo muestra el periodo y los campos que tendrá, para que el CU 01
    tenga a dónde redirigir. El CU 02 reemplaza esta vista con el formulario real.
    """
    periodo = get_object_or_404(
        Periodo.objects.select_related("proyecto"), pk=pk, proyecto__usuario=request.user
    )
    return render(request, "medidas/captura.html", {"periodo": periodo, "metricas": METRICAS})
