from django.urls import path

from . import views

app_name = "medidas"

urlpatterns = [
    path("medidas/", views.InicioCapturaView.as_view(), name="inicio"),
    path(
        "proyectos/<int:proyecto_id>/periodos/<int:periodo_id>/medidas/",
        views.CapturaMedidasView.as_view(),
        name="captura",
    ),
]
