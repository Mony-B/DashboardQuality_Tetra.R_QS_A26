from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("reportes/", views.reportes_view, name="reportes"),
]
