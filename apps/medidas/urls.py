from django.urls import path

from . import views

app_name = "medidas"

urlpatterns = [
    path("<int:pk>/medidas/", views.captura_medidas_view, name="captura"),
]
