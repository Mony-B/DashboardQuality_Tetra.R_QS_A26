"""Pruebas del CU 02 · Registrar las medidas del periodo (R5, R6, R7, R21)."""

from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.medidas.forms import MedidasPeriodoForm
from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()

MEDIDAS_VALIDAS = {
    "funciones_requeridas": "10",
    "funciones_entregadas": "8",
    "casos_ejecutados": "42",
    "casos_aprobados": "39",
    "requisitos_verificables": "25",
    "requisitos_con_prueba": "21",
    "defectos_codigo": "14",
    "kloc": "3.2",
}


class BaseCapturaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        cls.beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", "Clave-segura-123")
        cls.proyecto = Proyecto.objects.create(
            usuario=cls.ana, nombre="Dashboard SQA", marco_trabajo="Kanban"
        )
        cls.periodo = Periodo.objects.create(
            proyecto=cls.proyecto,
            nombre="Entrega 1",
            fecha_inicio=date(2026, 12, 12),
            fecha_fin=date(2026, 12, 24),
        )
        cls.url = reverse(
            "medidas:captura",
            kwargs={"proyecto_id": cls.proyecto.pk, "periodo_id": cls.periodo.pk},
        )

    def setUp(self):
        self.client.force_login(self.ana)

    def enviar(self, **cambios):
        datos = {**MEDIDAS_VALIDAS, **cambios}
        return self.client.post(self.url, datos)


class PantallaTests(BaseCapturaTests):
    def test_muestra_los_cuatro_bloques_con_formula_y_unidad(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        for titulo in (
            "Capacidad funcional",
            "Casos de prueba aprobados",
            "Cobertura de pruebas",
            "Densidad de defectos",
        ):
            self.assertContains(respuesta, titulo)
        self.assertContains(respuesta, "Fórmula:", count=4)
        self.assertContains(respuesta, "defectos/KLOC")
        self.assertContains(respuesta, "Guardar medidas")
        self.assertContains(respuesta, "Cancelar")

    def test_periodo_sin_medidas_muestra_el_texto_de_primera_captura(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Este periodo todavía no tiene medidas")

    def test_periodo_con_medidas_muestra_sus_valores_y_el_texto_de_correccion(self):
        self.periodo.funciones_requeridas = 10
        self.periodo.kloc = Decimal("3.2")
        self.periodo.save()
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Corrige las medidas capturadas anteriormente")
        self.assertContains(respuesta, 'value="10"')

    def test_dialogos_de_confirmacion_con_los_textos_del_diseno(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Se perderán los cambios sin guardar. ¿Deseas cancelar?")
        self.assertContains(respuesta, "Se perderán los cambios sin guardar. ¿Deseas continuar?")
        for boton in ("Sí, cancelar", "Sí, continuar", "Seguir editando"):
            self.assertContains(respuesta, boton)

    def test_el_formulario_lleva_proteccion_csrf(self):
        self.assertContains(self.client.get(self.url), "csrfmiddlewaretoken")


class AccesoTests(BaseCapturaTests):
    def test_sin_sesion_pide_iniciar_sesion(self):
        self.client.logout()
        respuesta = self.client.get(self.url)
        self.assertRedirects(
            respuesta,
            f"{reverse('cuentas:iniciar_sesion')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_periodo_de_otro_usuario_responde_404_al_ver_y_al_guardar(self):
        self.client.force_login(self.beto)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.enviar().status_code, 404)
        self.periodo.refresh_from_db()
        self.assertIsNone(self.periodo.funciones_requeridas)

    def test_periodo_que_no_pertenece_al_proyecto_de_la_url_responde_404(self):
        otro = Proyecto.objects.create(usuario=self.ana, nombre="Otro", marco_trabajo="Scrum")
        url = reverse(
            "medidas:captura", kwargs={"proyecto_id": otro.pk, "periodo_id": self.periodo.pk}
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_el_menu_abre_el_periodo_actual_del_proyecto(self):
        respuesta = self.client.get(reverse("medidas:inicio"))
        self.assertRedirects(respuesta, self.url)

    def test_el_menu_sin_proyectos_regresa_a_mis_proyectos(self):
        self.client.force_login(self.beto)
        respuesta = self.client.get(reverse("medidas:inicio"))
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))


class GuardarTests(BaseCapturaTests):
    """R5 y R7: guardar las ocho medidas y recalcular."""

    def test_guarda_las_ocho_medidas(self):
        respuesta = self.enviar()
        self.assertRedirects(respuesta, self.url)
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.funciones_requeridas, 10)
        self.assertEqual(self.periodo.funciones_entregadas, 8)
        self.assertEqual(self.periodo.casos_ejecutados, 42)
        self.assertEqual(self.periodo.casos_aprobados, 39)
        self.assertEqual(self.periodo.requisitos_verificables, 25)
        self.assertEqual(self.periodo.requisitos_con_prueba, 21)
        self.assertEqual(self.periodo.defectos_codigo, 14)
        self.assertEqual(self.periodo.kloc, Decimal("3.2"))

    def test_muestra_medidas_guardadas_y_conserva_los_valores(self):
        respuesta = self.enviar()
        respuesta = self.client.get(respuesta.url)
        self.assertContains(respuesta, "Medidas guardadas.")
        self.assertContains(respuesta, 'value="42"')

    def test_recalcula_la_salud_al_guardar(self):
        with mock.patch.object(Periodo, "recalcular_salud") as recalcular:
            self.enviar()
        recalcular.assert_called_once()

    def test_no_recalcula_si_las_medidas_son_invalidas(self):
        with mock.patch.object(Periodo, "recalcular_salud") as recalcular:
            self.enviar(casos_aprobados="50")
        recalcular.assert_not_called()

    def test_corregir_reemplaza_el_conjunto_anterior(self):
        """FA-3: se guarda un único conjunto de medidas por periodo."""
        self.enviar(funciones_requeridas="10", funciones_entregadas="4")
        self.enviar(funciones_requeridas="10", funciones_entregadas="8")
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.funciones_entregadas, 8)
        self.assertEqual(Periodo.objects.count(), 1)

    def test_kloc_decimal_se_guarda(self):
        self.enviar(kloc="2.5")
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.kloc, Decimal("2.5"))

    def test_30_defectos_en_2_kloc_es_valido(self):
        """Requisito especial 4: no se restringe la relación entre defectos y KLOC."""
        respuesta = self.enviar(defectos_codigo="30", kloc="2")
        self.assertRedirects(respuesta, self.url)

    def test_numerador_igual_al_total_es_valido(self):
        respuesta = self.enviar(casos_ejecutados="10", casos_aprobados="10")
        self.assertRedirects(respuesta, self.url)


class ValidacionTests(BaseCapturaTests):
    """R6 y FA-1: nada se guarda y el mensaje sale junto al campo."""

    def verificar_rechazo(self, campo, mensaje, **cambios):
        respuesta = self.enviar(**cambios)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(mensaje, respuesta.context["form"].errors[campo])
        self.assertContains(respuesta, mensaje)
        self.assertContains(respuesta, "No se guardó.")
        self.periodo.refresh_from_db()
        self.assertIsNone(self.periodo.funciones_requeridas)
        return respuesta

    def test_cada_medida_vacia_se_rechaza(self):
        """Las ocho medidas son obligatorias; las demás no se guardan."""
        for campo in MEDIDAS_VALIDAS:
            with self.subTest(campo=campo):
                respuesta = self.enviar(**{campo: ""})
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(
                    respuesta.context["form"].errors[campo], ["Este campo es obligatorio."]
                )
                self.assertContains(respuesta, "Este campo es obligatorio.")
                self.periodo.refresh_from_db()
                self.assertFalse(self.periodo.tiene_medidas())

    def test_todo_vacio_marca_las_ocho_medidas(self):
        datos = {nombre: "" for nombre in MEDIDAS_VALIDAS}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.context["form"].errors), set(MEDIDAS_VALIDAS))

    def test_una_medida_vacia_no_cambia_lo_guardado(self):
        self.enviar()
        self.enviar(funciones_entregadas="1", kloc="")
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.funciones_entregadas, 8)
        self.assertEqual(self.periodo.kloc, Decimal("3.2"))

    def test_conteo_negativo(self):
        self.verificar_rechazo(
            "funciones_requeridas", "El valor no puede ser negativo.", funciones_requeridas="-1"
        )

    def test_conteo_no_entero(self):
        self.verificar_rechazo(
            "casos_ejecutados",
            "Escribe un número entero, sin decimales.",
            casos_ejecutados="2.5",
        )

    def test_conteo_con_texto(self):
        self.verificar_rechazo(
            "defectos_codigo", "Escribe un número entero, sin decimales.", defectos_codigo="abc"
        )

    def test_kloc_igual_a_cero(self):
        self.verificar_rechazo("kloc", "El KLOC debe ser mayor que 0.", kloc="0")

    def test_kloc_negativo(self):
        self.verificar_rechazo("kloc", "El KLOC debe ser mayor que 0.", kloc="-1")

    def test_funciones_entregadas_mayores_que_las_requeridas(self):
        self.verificar_rechazo(
            "funciones_entregadas",
            "Las funciones entregadas no pueden ser más que las requeridas.",
            funciones_requeridas="10",
            funciones_entregadas="12",
        )

    def test_casos_aprobados_mayores_que_los_ejecutados(self):
        self.verificar_rechazo(
            "casos_aprobados",
            "Los casos aprobados no pueden ser más que los ejecutados.",
            casos_ejecutados="10",
            casos_aprobados="12",
        )

    def test_requisitos_con_prueba_mayores_que_los_verificables(self):
        self.verificar_rechazo(
            "requisitos_con_prueba",
            "Los requisitos con prueba no pueden ser más que los verificables.",
            requisitos_verificables="10",
            requisitos_con_prueba="11",
        )

    def test_conserva_lo_capturado_al_rechazar(self):
        respuesta = self.enviar(casos_aprobados="50")
        self.assertContains(respuesta, 'value="42"')
        self.assertContains(respuesta, 'value="50"')

    def test_todo_o_nada_un_error_impide_guardar_las_demas(self):
        self.enviar(kloc="0")
        self.periodo.refresh_from_db()
        self.assertFalse(self.periodo.tiene_medidas())

    def test_un_envio_invalido_no_cambia_lo_guardado(self):
        self.enviar()
        self.enviar(funciones_entregadas="99")
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.funciones_entregadas, 8)

    def test_varios_errores_a_la_vez_se_muestran_junto_a_cada_campo(self):
        respuesta = self.enviar(funciones_entregadas="12", casos_aprobados="", kloc="0")
        errores = respuesta.context["form"].errors
        self.assertEqual(set(errores), {"funciones_entregadas", "kloc"})


class FormularioTests(TestCase):
    def test_bloques_enlazan_los_ocho_campos(self):
        form = MedidasPeriodoForm()
        campos = [campo.name for bloque in form.bloques() for campo, _ in bloque["campos"]]
        self.assertEqual(len(campos), 8)
        self.assertEqual(len(set(campos)), 8)
