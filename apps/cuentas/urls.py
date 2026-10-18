from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("iniciar-sesion/", views.IniciarSesionView.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", views.CerrarSesionView.as_view(), name="cerrar_sesion"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
]
