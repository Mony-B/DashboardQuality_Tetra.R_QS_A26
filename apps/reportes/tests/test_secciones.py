"""Pruebas de las secciones del reporte (CU 05). No necesitan base de datos."""

from decimal import Decimal
from unittest import TestCase

from apps.reportes import secciones as s
from apps.tablero.calculo import Medidas


class ElegidasTests(TestCase):
    def test_sin_envio_vienen_las_cuatro_marcadas(self):
        self.assertEqual(
            s.elegidas([], enviado=False), ["resumen", "metricas", "medidas", "actividades"]
        )

    def test_con_envio_solo_las_elegidas_en_el_orden_del_reporte(self):
        self.assertEqual(
            s.elegidas(["actividades", "resumen"], enviado=True), ["resumen", "actividades"]
        )

    def test_con_envio_y_ninguna_no_hay_secciones(self):
        self.assertEqual(s.elegidas([], enviado=True), [])

    def test_ignora_claves_desconocidas_y_repetidas(self):
        self.assertEqual(
            s.elegidas(["medidas", "medidas", "inventada", "<script>"], enviado=True), ["medidas"]
        )

    def test_las_cuatro_secciones_del_requisito_r19(self):
        self.assertEqual(
            [texto for _, texto in s.SECCIONES],
            [
                "Resumen de salud (índice y estado general)",
                "Métricas y su aporte al índice",
                "Medidas del periodo",
                "Actividades SQA",
            ],
        )


class MedidasTests(TestCase):
    def test_ocho_filas_con_sus_valores(self):
        medidas = Medidas(10, 9, 25, 24, 20, 17, 7, Decimal("2.000"))
        filas = s.filas_medidas(medidas)
        self.assertEqual(len(filas), 8)
        self.assertEqual(filas[0], ("Funciones requeridas del periodo", "10"))
        self.assertEqual(filas[7], ("Tamaño del código (KLOC)", "2.0"))

    def test_cero_se_muestra_y_vacio_es_sin_dato(self):
        filas = dict(s.filas_medidas(Medidas(funciones_requeridas=0)))
        self.assertEqual(filas["Funciones requeridas del periodo"], "0")
        self.assertEqual(filas["Funciones entregadas y aceptadas"], "sin dato")

    def test_kloc_conserva_sus_decimales(self):
        filas = dict(s.filas_medidas(Medidas(kloc=Decimal("1.250"))))
        self.assertEqual(filas["Tamaño del código (KLOC)"], "1.25")


class EnlaceTests(TestCase):
    def test_solo_http_y_https_son_vinculo(self):
        enlace = "https://drive.google.com/x"
        self.assertEqual(s.enlace_seguro(enlace), enlace)
        self.assertEqual(s.enlace_seguro("HTTP://ejemplo.com"), "HTTP://ejemplo.com")

    def test_otros_esquemas_o_vacio_no_son_vinculo(self):
        invalidos = (
            "",
            None,
            "javascript:alert(1)",
            "data:text/html,x",
            "ftp://x",
            "drive.google.com",
        )
        for valor in invalidos:
            self.assertEqual(s.enlace_seguro(valor), "")
