from django.urls import path

from . import views

app_name = "tablero"

urlpatterns = [
    path("dashboard/", views.dashboard_salud_view, name="dashboard"),
]
