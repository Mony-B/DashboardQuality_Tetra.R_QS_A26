"""Pruebas del CU 04 · Dashboard (R10–R18, R21). Flujo normal y flujos alternativos."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.actividades.models import Actividad
from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()
CLAVE = "Clave-segura-123"
URL = reverse("tablero:dashboard")

# M1 90 %, M2 96 %, M3 85 %, M4 3.5 → índice 72, «En riesgo» (ejemplo de la especificación).
MEDIDAS_72 = {
    "funciones_requeridas": 10,
    "funciones_entregadas": 9,
    "casos_ejecutados": 25,
    "casos_aprobados": 24,
    "requisitos_verificables": 20,
    "requisitos_con_prueba": 17,
    "defectos_codigo": 7,
    "kloc": Decimal("2"),
}
MEDIDAS_100 = {
    "funciones_requeridas": 10,
    "funciones_entregadas": 10,
    "casos_ejecutados": 20,
    "casos_aprobados": 20,
    "requisitos_verificables": 20,
    "requisitos_con_prueba": 20,
    "defectos_codigo": 2,
    "kloc": Decimal("1"),
}


class BaseDashboard(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", CLAVE)
        self.beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        self.client.force_login(self.ana)
        self.proyecto = Proyecto.objects.create(
            usuario=self.ana, nombre="QuaQlity", marco_trabajo="Kanban"
        )

    def periodo(self, nombre="Entrega 1", inicio=(12, 12), fin=(12, 24), proyecto=None, **medidas):
        return Periodo.objects.create(
            proyecto=proyecto or self.proyecto,
            nombre=nombre,
            fecha_inicio=date(2026, *inicio),
            fecha_fin=date(2026, *fin),
            **medidas,
        )


class FlujoNormalTests(BaseDashboard):
    def test_muestra_indice_estado_y_cuatro_metricas(self):
        periodo = self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL, {"proyecto": self.proyecto.pk, "periodo": periodo.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "72.0")
        self.assertContains(respuesta, "En riesgo")
        for texto in (
            "M1 · Capacidad funcional",
            "M2 · Tasa de aprobación de pruebas",
            "M3 · Cobertura de requisitos por pruebas",
            "M4 · Densidad de defectos",
        ):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, "60 pts × 25 % = 15.0 al índice")
        self.assertContains(respuesta, "100 pts × 30 % = 30.0 al índice")
        self.assertContains(respuesta, "Peso: 30 %")

    def test_metrica_amarilla_muestra_motivo_y_umbral(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "Amarillo: 90.0 % es menor que 95 %.")
        self.assertContains(respuesta, "Amarillo: 3.5 supera 2.")

    def test_metrica_roja_muestra_motivo_con_el_umbral_del_amarillo(self):
        self.periodo(**{**MEDIDAS_100, "casos_aprobados": 10})  # M2 = 50 %
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "Rojo: 50.0 % es menor que 85 %.")

    def test_todo_en_verde_es_saludable_100(self):
        self.periodo(**MEDIDAS_100)
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "100.0")
        self.assertContains(respuesta, "Saludable")
        self.assertContains(respuesta, "las cuatro métricas están en verde")

    def test_por_omision_abre_el_periodo_actual_del_proyecto(self):
        self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        self.periodo("Entrega 2", (12, 12), (12, 24), **MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.context["periodo"].nombre, "Entrega 2")
        self.assertContains(respuesta, "72.0")

    def test_muestra_tabla_de_umbrales_y_pesos(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "Reglas de evaluación")
        self.assertContains(respuesta, "Pesos: 25 %, 30 %, 20 %, 25 %.")
        self.assertContains(respuesta, "Las actividades SQA no afectan el índice.")

    def test_consultar_no_modifica_las_medidas(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.client.get(URL, {"periodo": periodo.pk})
        periodo.refresh_from_db()
        self.assertEqual(periodo.funciones_entregadas, 9)
        self.assertEqual(periodo.kloc, Decimal("2"))

    def test_solo_acepta_lectura(self):
        self.periodo(**MEDIDAS_72)
        self.assertEqual(self.client.post(URL).status_code, 405)

    def test_el_menu_lleva_al_dashboard(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, f'href="{URL}"')


class SinDatosTests(BaseDashboard):
    """FA-1: nunca se inventa un valor ni hay división entre cero."""

    def test_periodo_sin_medidas_es_sin_evaluar(self):
        self.periodo()
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Sin evaluar")
        self.assertContains(respuesta, "Sin datos")
        self.assertContains(respuesta, "Falta registrar las funciones entregadas")
        self.assertIsNone(respuesta.context["indice"])

    def test_denominador_cero_indica_cual_medida_es_cero(self):
        self.periodo(**{**MEDIDAS_72, "funciones_requeridas": 0, "funciones_entregadas": 0})
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "el total de las funciones requeridas del periodo es 0")

    def test_las_demas_metricas_con_datos_se_muestran(self):
        self.periodo(**{**MEDIDAS_72, "funciones_requeridas": None})
        respuesta = self.client.get(URL)
        self.assertContains(respuesta, "Falta registrar las funciones requeridas del periodo.")
        self.assertContains(respuesta, "96.0")  # M2 sigue visible
        self.assertContains(respuesta, "Sin evaluar")
        self.assertIsNone(respuesta.context["indice"])

    def test_kloc_cero_no_rompe_la_pantalla(self):
        # La base no admite KLOC = 0 (restricción); un KLOC vacío es «sin datos».
        self.periodo(**{**MEDIDAS_72, "kloc": None})
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Falta registrar el tamaño del código (KLOC).")


class SeleccionTests(BaseDashboard):
    """FA-3: cambiar de proyecto o de periodo recalcula, sin confirmación."""

    def test_cambiar_de_periodo(self):
        p1 = self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        self.periodo("Entrega 2", (12, 12), (12, 24), **MEDIDAS_72)
        respuesta = self.client.get(URL, {"periodo": p1.pk})
        self.assertEqual(respuesta.context["periodo"], p1)
        self.assertContains(respuesta, "Saludable")

    def test_cambiar_de_proyecto_abre_su_periodo_actual(self):
        self.periodo(**MEDIDAS_72)
        otro = Proyecto.objects.create(usuario=self.ana, nombre="Otro", marco_trabajo="Scrum")
        actual = self.periodo("Iteración 2", (12, 20), (12, 31), proyecto=otro, **MEDIDAS_100)
        respuesta = self.client.get(URL, {"proyecto": otro.pk})
        self.assertEqual(respuesta.context["periodo"], actual)

    def test_sin_proyectos_vuelve_a_mis_proyectos(self):
        self.proyecto.delete()
        respuesta = self.client.get(URL)
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))

    def test_proyecto_sin_periodos_vuelve_a_mis_proyectos(self):
        respuesta = self.client.get(URL, {"proyecto": self.proyecto.pk})
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))

    def test_identificador_no_numerico_es_404(self):
        self.periodo(**MEDIDAS_72)
        self.assertEqual(self.client.get(URL, {"periodo": "abc"}).status_code, 404)
        self.assertEqual(self.client.get(URL, {"proyecto": "x"}).status_code, 404)

    def test_periodo_de_otro_proyecto_del_usuario_con_proyecto_distinto_es_404(self):
        periodo = self.periodo(**MEDIDAS_72)
        otro = Proyecto.objects.create(usuario=self.ana, nombre="Otro", marco_trabajo="Scrum")
        respuesta = self.client.get(URL, {"proyecto": otro.pk, "periodo": periodo.pk})
        self.assertEqual(respuesta.status_code, 404)


class AccesoTests(BaseDashboard):
    """Requisito especial 1 (R20, R21): solo el dueño ve su Dashboard."""

    def test_sin_sesion_redirige_al_acceso(self):
        self.client.logout()
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("iniciar", respuesta["Location"])

    def test_periodo_ajeno_responde_404(self):
        ajeno = Proyecto.objects.create(usuario=self.beto, nombre="De Beto", marco_trabajo="XP")
        periodo = self.periodo(proyecto=ajeno, **MEDIDAS_72)
        self.periodo(**MEDIDAS_100)
        self.assertEqual(self.client.get(URL, {"periodo": periodo.pk}).status_code, 404)

    def test_proyecto_ajeno_responde_404(self):
        ajeno = Proyecto.objects.create(usuario=self.beto, nombre="De Beto", marco_trabajo="XP")
        self.periodo(**MEDIDAS_100)
        self.assertEqual(self.client.get(URL, {"proyecto": ajeno.pk}).status_code, 404)

    def test_no_lista_proyectos_ajenos_en_el_selector(self):
        Proyecto.objects.create(usuario=self.beto, nombre="Secreto de Beto", marco_trabajo="XP")
        self.periodo(**MEDIDAS_100)
        self.assertNotContains(self.client.get(URL), "Secreto de Beto")


class TendenciaTests(BaseDashboard):
    def test_un_punto_por_periodo_en_orden_cronologico(self):
        self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        self.periodo("Entrega 2", (12, 12), (12, 24), **MEDIDAS_72)
        respuesta = self.client.get(URL, {"metrica": "capacidad_funcional"})
        puntos = respuesta.context["tendencia"]["puntos"]
        self.assertEqual([p["etiqueta"] for p in puntos], ["Entrega 1", "Entrega 2"])
        self.assertEqual([p["texto"] for p in puntos], ["100.0", "90.0"])
        self.assertEqual([p["semaforo"] for p in puntos], ["verde", "amarillo"])
        self.assertNotContains(respuesta, "solo tiene un periodo")

    def test_elegir_otra_metrica_cambia_la_grafica(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL, {"metrica": "densidad_defectos"})
        self.assertEqual(respuesta.context["definicion"].clave, "densidad_defectos")
        self.assertEqual(respuesta.context["tendencia"]["puntos"][0]["texto"], "3.5")

    def test_metrica_desconocida_usa_la_primera(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL, {"metrica": "inventada"})
        self.assertEqual(respuesta.context["definicion"].clave, "capacidad_funcional")

    def test_fa4_un_solo_periodo_avisa_que_faltan_periodos(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertEqual(len(respuesta.context["tendencia"]["puntos"]), 1)
        self.assertContains(respuesta, "solo tiene un periodo")
        self.assertContains(respuesta, "Se necesitan más periodos para ver una tendencia.")

    def test_fa5_periodo_sin_datos_no_dibuja_punto_ni_cuenta_como_cero(self):
        self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        self.periodo("Iteración 2", (12, 12), (12, 20))
        self.periodo("Entrega 3", (12, 22), (12, 31), **MEDIDAS_72)
        respuesta = self.client.get(URL, {"metrica": "capacidad_funcional"})
        grafica = respuesta.context["tendencia"]
        self.assertEqual(grafica["periodos_sin_datos"], ["Iteración 2"])
        self.assertTrue(grafica["puntos"][1]["sin_datos"])
        self.assertNotIn("y", grafica["puntos"][1])
        self.assertContains(respuesta, "Iteración 2: sin datos")
        self.assertEqual(grafica["segmentos"], [])  # no se une 1 con 3 a través del hueco

    def test_el_proyecto_no_mezcla_periodos_de_otros(self):
        self.periodo(**MEDIDAS_72)
        otro = Proyecto.objects.create(usuario=self.ana, nombre="Otro", marco_trabajo="Scrum")
        self.periodo("Otro periodo", (12, 1), (12, 5), proyecto=otro, **MEDIDAS_100)
        respuesta = self.client.get(URL, {"proyecto": self.proyecto.pk})
        self.assertEqual(len(respuesta.context["tendencia"]["puntos"]), 1)


class ActividadesNoAfectanTests(BaseDashboard):
    """Requisito especial 7: las actividades SQA no cambian métricas ni índice."""

    def test_agregar_una_actividad_no_cambia_el_indice(self):
        periodo = self.periodo(**MEDIDAS_72)
        antes = self.client.get(URL).context["indice"]
        Actividad.objects.create(
            periodo=periodo,
            tecnica="revision_pares",
            artefacto="CU 04",
            responsable="Ana",
            fecha=date(2026, 12, 16),
        )
        self.assertEqual(self.client.get(URL).context["indice"], antes)


class RecalculoTests(BaseDashboard):
    def test_recalcular_salud_refleja_lo_ultimo_guardado(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.assertEqual(periodo.recalcular_salud().indice, Decimal("72"))
        periodo.funciones_entregadas = 10
        periodo.save()
        self.assertEqual(periodo.recalcular_salud().indice, Decimal("82"))
