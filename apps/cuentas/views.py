from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from .forms import RegistroForm


class IniciarSesionView(auth_views.LoginView):
    template_name = "cuentas/iniciar_sesion.html"
    redirect_authenticated_user = True


class CerrarSesionView(auth_views.LogoutView):
    """Solo acepta POST (con token CSRF), como exige Django 5."""


@method_decorator(login_not_required, name="dispatch")
class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "cuentas/registro.html"
    success_url = reverse_lazy("proyectos:mis_proyectos")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        login(self.request, self.object)
        return respuesta
