from django.urls import path

from . import views

app_name = "actividades"

urlpatterns = [
    path("actividades/", views.inicio_actividades_view, name="inicio"),
    path("periodos/<int:periodo_id>/actividades/", views.actividades_view, name="lista"),
    path(
        "periodos/<int:periodo_id>/actividades/nueva/",
        views.planear_actividad_view,
        name="nueva",
    ),
    path("actividades/<int:actividad_id>/editar/", views.editar_actividad_view, name="editar"),
    path("actividades/<int:actividad_id>/estado/", views.cambiar_estado_view, name="estado"),
    path("actividades/<int:actividad_id>/enlace/", views.guardar_enlace_view, name="enlace"),
]
