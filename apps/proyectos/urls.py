from django.urls import path

from . import views

app_name = "proyectos"

urlpatterns = [
    path("proyectos/", views.MisProyectosView.as_view(), name="mis_proyectos"),
]
