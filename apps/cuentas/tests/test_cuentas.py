"""Pruebas de acceso (R1) y almacenamiento de contraseñas (R22)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()
CLAVE = "Clave-segura-123"


class RegistroTests(TestCase):
    def _registrar(self, username="ana", email="ana@ejemplo.com"):
        return self.client.post(
            reverse("cuentas:registro"),
            {"username": username, "email": email, "password1": CLAVE, "password2": CLAVE},
        )

    def test_crear_cuenta_inicia_sesion_y_redirige(self):
        respuesta = self._registrar()
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))
        self.assertTrue(Usuario.objects.filter(username="ana").exists())

    def test_correo_repetido_se_rechaza(self):
        self._registrar()
        self.client.logout()
        respuesta = self._registrar(username="otra", email="ANA@ejemplo.com")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFormError(
            respuesta.context["form"], "email", "Ya existe una cuenta con este correo."
        )
        self.assertEqual(Usuario.objects.count(), 1)

    def test_contrasena_no_se_guarda_en_texto_plano(self):
        self._registrar()
        usuario = Usuario.objects.get(username="ana")
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertTrue(usuario.check_password(CLAVE))


class SesionTests(TestCase):
    def setUp(self):
        Usuario.objects.create_user("ana", "ana@ejemplo.com", CLAVE)

    def test_iniciar_sesion_correcto(self):
        respuesta = self.client.post(
            reverse("cuentas:iniciar_sesion"), {"username": "ana", "password": CLAVE}
        )
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))

    def test_contrasena_incorrecta_no_entra(self):
        respuesta = self.client.post(
            reverse("cuentas:iniciar_sesion"), {"username": "ana", "password": "otra"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cerrar_sesion(self):
        self.client.login(username="ana", password=CLAVE)
        respuesta = self.client.post(reverse("cuentas:cerrar_sesion"))
        self.assertRedirects(respuesta, reverse("cuentas:iniciar_sesion"))
        self.assertNotIn("_auth_user_id", self.client.session)
