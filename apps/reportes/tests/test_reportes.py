"""Pruebas del CU 05 · Reportes (R19, R21). Flujo normal, FA-1 a FA-5 y FE-1 a FE-3."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.actividades.models import Actividad
from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()
CLAVE = "Clave-segura-123"
URL = reverse("reportes:reportes")
TODAS = ["resumen", "metricas", "medidas", "actividades"]

# M1 90 %, M2 96 %, M3 85 %, M4 3.5 → índice 72, «En riesgo».
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


class BaseReportes(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", CLAVE)
        self.beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        self.client.force_login(self.ana)
        self.proyecto = Proyecto.objects.create(
            usuario=self.ana, nombre="QuaQlity", marco_trabajo="Scrum"
        )

    def periodo(self, nombre="Entrega 3", inicio=(12, 12), fin=(12, 24), proyecto=None, **medidas):
        return Periodo.objects.create(
            proyecto=proyecto or self.proyecto,
            nombre=nombre,
            fecha_inicio=date(2026, *inicio),
            fecha_fin=date(2026, *fin),
            **medidas,
        )

    def generar(self, periodo, secciones=TODAS, proyecto=None, **extra):
        datos = {
            "proyecto": (proyecto or periodo.proyecto).pk,
            "periodo": periodo.pk,
            "enviado": "1",
            "generar": "1",
            "secciones": secciones,
            **extra,
        }
        return self.client.get(URL, datos)

    def actividad(self, periodo, **cambios):
        datos = {
            "periodo": periodo,
            "tecnica": "revision_pares",
            "artefacto": "CU 04",
            "responsable": "Integrante 2",
            "fecha": date(2026, 12, 16),
        }
        return Actividad.objects.create(**{**datos, **cambios})


class FormularioTests(BaseReportes):
    def test_formulario_con_las_cuatro_secciones_marcadas(self):
        self.periodo(**MEDIDAS_72)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "reportes/formulario.html")
        self.assertContains(respuesta, "Generar reporte")
        self.assertContains(respuesta, "Resumen de salud (índice y estado general)")
        self.assertContains(respuesta, "Métricas y su aporte al índice")
        self.assertContains(respuesta, "Medidas del periodo")
        self.assertContains(respuesta, 'type="checkbox"', count=4)
        self.assertContains(respuesta, " checked>", count=4)

    def test_abrir_reportes_no_genera_nada(self):
        self.periodo(**MEDIDAS_72)
        self.assertTemplateNotUsed(self.client.get(URL), "reportes/reporte_salud.html")

    def test_por_omision_el_periodo_es_el_actual(self):
        self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        actual = self.periodo("Entrega 2", (12, 12), (12, 24), **MEDIDAS_72)
        self.assertEqual(self.client.get(URL).context["periodo"], actual)

    def test_el_formulario_conserva_lo_elegido_al_regenerar(self):
        periodo = self.periodo(**MEDIDAS_72)
        respuesta = self.generar(periodo, secciones=[])
        self.assertEqual(respuesta.context["periodo"], periodo)
        self.assertEqual(respuesta.context["proyecto"], self.proyecto)

    def test_el_menu_lleva_a_reportes(self):
        self.periodo(**MEDIDAS_72)
        self.assertContains(self.client.get(URL), f'href="{URL}"')

    def test_sin_proyectos_vuelve_a_mis_proyectos(self):
        self.proyecto.delete()
        self.assertRedirects(self.client.get(URL), reverse("proyectos:mis_proyectos"))

    def test_cambiar_de_proyecto_conserva_las_secciones_elegidas(self):
        self.periodo(**MEDIDAS_72)
        datos = {"proyecto": self.proyecto.pk, "enviado": "1", "secciones": ["medidas"]}
        respuesta = self.client.get(URL, datos)
        self.assertContains(respuesta, " checked>", count=1)


class FlujoNormalTests(BaseReportes):
    def test_reporte_con_encabezado_y_las_cuatro_secciones(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.actividad(periodo, estado="completada", enlace_evidencia="https://drive.google.com/e")
        self.actividad(periodo, tecnica="analisis_estatico", artefacto="Módulo dashboard")
        respuesta = self.generar(periodo)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "reportes/reporte_salud.html")
        for texto in (
            "Reporte de salud",
            "QuaQlity",
            "Scrum",
            "Entrega 3 (12/12/2026 – 24/12/2026)",
            f"{timezone.localdate():%d/%m/%Y}",
            "ana",
            "72.0",
            "En riesgo",
        ):
            self.assertContains(respuesta, texto)
        for id_seccion in ("sec-resumen", "sec-metricas", "sec-medidas", "sec-actividades"):
            self.assertContains(respuesta, f'id="{id_seccion}"')

    def test_tabla_de_metricas_con_valor_semaforo_peso_y_aporte(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=["metricas"])
        self.assertContains(respuesta, "M1 · Capacidad funcional")
        self.assertContains(respuesta, "90.0 %")
        self.assertContains(respuesta, "3.5 defectos/KLOC")
        self.assertContains(respuesta, "Amarillo")
        self.assertContains(respuesta, "30 %")
        self.assertContains(respuesta, "<td>30.0</td>")

    def test_medidas_del_periodo(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=["medidas"])
        self.assertContains(respuesta, "Funciones requeridas del periodo")
        self.assertContains(respuesta, "Tamaño del código (KLOC)")
        self.assertContains(respuesta, "<td>2.0</td>")

    def test_actividades_con_enlace_y_sin_enlace(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.actividad(periodo, enlace_evidencia="https://drive.google.com/e")
        self.actividad(periodo, artefacto="Módulo dashboard")
        respuesta = self.generar(periodo, secciones=["actividades"])
        self.assertContains(respuesta, "Revisión entre pares")
        self.assertContains(respuesta, 'href="https://drive.google.com/e"')
        self.assertContains(respuesta, "Abrir evidencia", count=1)
        self.assertContains(respuesta, "Sin enlace", count=1)
        self.assertContains(respuesta, "no forman parte del índice de salud")

    def test_un_enlace_que_no_es_http_no_se_vuelve_vinculo(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.actividad(periodo, enlace_evidencia="javascript:alert(1)")
        respuesta = self.generar(periodo, secciones=["actividades"])
        self.assertNotContains(respuesta, "javascript:")
        self.assertContains(respuesta, "Sin enlace")

    def test_los_valores_coinciden_con_el_dashboard(self):
        periodo = self.periodo(**MEDIDAS_72)
        dashboard = self.client.get(reverse("tablero:dashboard"), {"periodo": periodo.pk})
        reporte = self.generar(periodo)
        self.assertEqual(reporte.context["indice"], dashboard.context["indice"])
        self.assertEqual(reporte.context["salud"].estado, dashboard.context["salud"].estado)
        self.assertEqual(
            [m["valor"] for m in reporte.context["metricas"]],
            [m["valor"] for m in dashboard.context["metricas"]],
        )

    def test_solo_muestra_las_secciones_elegidas(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=["resumen", "metricas"])
        self.assertContains(respuesta, 'id="sec-resumen"')
        self.assertContains(respuesta, 'id="sec-metricas"')
        self.assertNotContains(respuesta, 'id="sec-medidas"')
        self.assertNotContains(respuesta, 'id="sec-actividades"')
        self.assertContains(respuesta, "Generado por")  # el encabezado siempre aparece

    def test_las_secciones_salen_en_el_orden_del_reporte(self):
        respuesta = self.generar(
            self.periodo(**MEDIDAS_72), secciones=["actividades", "resumen"]
        ).content.decode()
        self.assertLess(respuesta.index("sec-resumen"), respuesta.index("sec-actividades"))

    def test_un_valor_desconocido_en_secciones_se_ignora(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=["resumen", "otra"])
        self.assertEqual(respuesta.context["marcadas"], ["resumen"])

    def test_no_modifica_medidas_ni_actividades(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.actividad(periodo)
        self.generar(periodo)
        periodo.refresh_from_db()
        self.assertEqual(periodo.funciones_entregadas, 9)
        self.assertEqual(Actividad.objects.count(), 1)

    def test_las_actividades_no_cambian_el_indice(self):
        periodo = self.periodo(**MEDIDAS_72)
        antes = self.generar(periodo).context["indice"]
        self.actividad(periodo, estado="completada")
        self.assertEqual(self.generar(periodo).context["indice"], antes)


class FlujosAlternosTests(BaseReportes):
    def test_fa1_periodo_sin_medidas_no_genera_y_enlaza_a_captura(self):
        periodo = self.periodo()
        respuesta = self.generar(periodo)
        self.assertTemplateUsed(respuesta, "reportes/formulario.html")
        self.assertTemplateNotUsed(respuesta, "reportes/reporte_salud.html")
        self.assertContains(respuesta, "Este periodo no tiene medidas capturadas.")
        self.assertContains(respuesta, "para generar el reporte.")
        self.assertContains(respuesta, f'href="{periodo.get_absolute_url_medidas()}"')

    def test_fa2_ninguna_seccion_muestra_el_mensaje_junto_a_las_secciones(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=[])
        self.assertTemplateUsed(respuesta, "reportes/formulario.html")
        self.assertContains(respuesta, "Elige al menos una sección.")
        self.assertNotContains(respuesta, " checked>")

    def test_fa1_y_fa2_a_la_vez_muestran_los_dos_avisos(self):
        respuesta = self.generar(self.periodo(), secciones=[])
        self.assertContains(respuesta, "Elige al menos una sección.")
        self.assertContains(respuesta, "Este periodo no tiene medidas capturadas.")

    def test_fa3_metrica_sin_datos_da_indice_sin_calcular_y_sin_evaluar(self):
        periodo = self.periodo(**{**MEDIDAS_72, "casos_ejecutados": 0, "casos_aprobados": 0})
        respuesta = self.generar(periodo)
        self.assertTemplateUsed(respuesta, "reportes/reporte_salud.html")
        self.assertContains(respuesta, "sin datos")
        self.assertContains(respuesta, "índice sin calcular")
        self.assertContains(respuesta, "Sin evaluar")
        self.assertIsNone(respuesta.context["indice"])

    def test_fa4_sin_actividades_muestra_el_texto_de_la_seccion(self):
        respuesta = self.generar(self.periodo(**MEDIDAS_72), secciones=["actividades"])
        self.assertContains(respuesta, "No hay actividades SQA registradas en este periodo.")

    def test_fa5_otro_periodo_da_un_reporte_nuevo(self):
        p1 = self.periodo("Entrega 1", (12, 1), (12, 10), **MEDIDAS_100)
        p2 = self.periodo("Entrega 2", (12, 12), (12, 24), **MEDIDAS_72)
        self.assertEqual(self.generar(p1).context["indice"], "100.0")
        self.assertEqual(self.generar(p2).context["indice"], "72.0")

    def test_fa5_el_enlace_para_generar_otro_conserva_lo_elegido(self):
        periodo = self.periodo(**MEDIDAS_72)
        respuesta = self.generar(periodo, secciones=["resumen", "medidas"])
        self.assertContains(respuesta, "Generar otro reporte")
        self.assertContains(respuesta, f"proyecto={self.proyecto.pk}")
        self.assertContains(respuesta, "secciones=resumen")
        self.assertContains(respuesta, "secciones=medidas")


class ExcepcionesTests(BaseReportes):
    def test_fe2_periodo_ajeno_responde_404_y_no_muestra_datos(self):
        ajeno = Proyecto.objects.create(usuario=self.beto, nombre="Secreto", marco_trabajo="XP")
        periodo = self.periodo(proyecto=ajeno, **MEDIDAS_72)
        self.periodo("Mío", (11, 1), (11, 10), **MEDIDAS_100)
        datos = {"periodo": periodo.pk, "generar": "1", "secciones": TODAS}
        respuesta = self.client.get(URL, datos)
        self.assertEqual(respuesta.status_code, 404)
        self.assertNotContains(respuesta, "Secreto", status_code=404)

    def test_fe2_el_404_explica_y_ofrece_volver_a_reportes(self):
        respuesta = self.client.get(URL, {"periodo": 999999})
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "No encontramos este proyecto o periodo", status_code=404)
        self.assertContains(respuesta, "No existe o no es tuyo.", status_code=404)
        self.assertContains(respuesta, f'href="{URL}"', status_code=404)
        self.assertContains(respuesta, "Volver a Reportes", status_code=404)

    def test_fe2_proyecto_ajeno_responde_404(self):
        ajeno = Proyecto.objects.create(usuario=self.beto, nombre="Secreto", marco_trabajo="XP")
        self.periodo(**MEDIDAS_72)
        self.assertEqual(self.client.get(URL, {"proyecto": ajeno.pk}).status_code, 404)

    def test_fe2_periodo_que_no_es_del_proyecto_elegido_responde_404(self):
        periodo = self.periodo(**MEDIDAS_72)
        otro = Proyecto.objects.create(usuario=self.ana, nombre="Otro", marco_trabajo="Kanban")
        respuesta = self.client.get(URL, {"proyecto": otro.pk, "periodo": periodo.pk})
        self.assertEqual(respuesta.status_code, 404)

    def test_identificador_no_numerico_responde_404(self):
        self.periodo(**MEDIDAS_72)
        self.assertEqual(self.client.get(URL, {"periodo": "abc"}).status_code, 404)

    def test_fe2_no_lista_proyectos_ajenos_en_el_formulario(self):
        Proyecto.objects.create(usuario=self.beto, nombre="Secreto de Beto", marco_trabajo="XP")
        self.periodo(**MEDIDAS_72)
        self.assertNotContains(self.client.get(URL), "Secreto de Beto")

    def test_fe3_sin_sesion_redirige_a_iniciar_sesion(self):
        self.client.logout()
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("cuentas:iniciar_sesion"), respuesta["Location"])

    def test_fe3_un_reporte_por_url_sin_sesion_tampoco_se_muestra(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.client.logout()
        respuesta = self.generar(periodo)
        self.assertEqual(respuesta.status_code, 302)

    def test_solo_acepta_lectura(self):
        self.periodo(**MEDIDAS_72)
        self.assertEqual(self.client.post(URL, {"generar": "1"}).status_code, 405)

    def test_generar_el_mismo_reporte_dos_veces_no_crea_registros(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.actividad(periodo)
        self.generar(periodo)
        self.generar(periodo)
        self.assertEqual(Periodo.objects.count(), 1)
        self.assertEqual(Actividad.objects.count(), 1)
        self.assertEqual(Proyecto.objects.count(), 1)

    def test_fe1_abrir_reportes_y_salir_no_guarda_nada(self):
        periodo = self.periodo(**MEDIDAS_72)
        self.client.get(URL, {"periodo": periodo.pk, "enviado": "1", "secciones": ["resumen"]})
        self.assertEqual(Periodo.objects.count(), 1)
        self.assertEqual(Actividad.objects.count(), 0)
