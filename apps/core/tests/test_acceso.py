"""Pruebas del comportamiento común de acceso (R20, R21)."""

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic import ListView

from apps.core.mixins import PropietarioMixin

Usuario = get_user_model()


class SesionRequeridaTests(TestCase):
    """R20: sin sesión, toda pantalla manda a iniciar sesión."""

    def test_inicio_sin_sesion_redirige_a_iniciar_sesion(self):
        respuesta = self.client.get(reverse("core:inicio"))
        url_login = reverse("cuentas:iniciar_sesion")
        self.assertRedirects(respuesta, f"{url_login}?next=/")

    def test_inicio_con_sesion_responde_200(self):
        usuario = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(respuesta.status_code, 200)


class PropietarioMixinTests(TestCase):
    """R21: el mixin solo deja ver los objetos del usuario autenticado."""

    def test_filtra_por_usuario_autenticado(self):
        # LogEntry (del admin) sirve de modelo de prueba porque tiene FK al usuario.
        ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", "Clave-segura-123")
        de_ana = LogEntry.objects.create(user=ana, action_flag=ADDITION, object_repr="de ana")
        LogEntry.objects.create(user=beto, action_flag=ADDITION, object_repr="de beto")

        class VistaPrueba(PropietarioMixin, ListView):
            model = LogEntry
            campo_propietario = "user"

        peticion = RequestFactory().get("/")
        peticion.user = ana
        vista = VistaPrueba()
        vista.setup(peticion)

        self.assertQuerySetEqual(vista.get_queryset(), [de_ana])
