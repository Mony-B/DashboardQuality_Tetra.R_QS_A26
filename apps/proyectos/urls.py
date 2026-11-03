from django.urls import path

from . import views

app_name = "proyectos"

urlpatterns = [
    path("", views.mis_proyectos_view, name="mis_proyectos"),
    path("nuevo/", views.nuevo_proyecto_view, name="nuevo"),
    path("<int:pk>/periodos/nuevo/", views.nuevo_periodo_view, name="nuevo_periodo"),
]
