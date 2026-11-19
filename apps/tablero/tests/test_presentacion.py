"""Pruebas de la gráfica y de los textos del Dashboard (CU 04). No necesitan base de datos."""

from decimal import Decimal
from unittest import TestCase

from apps.tablero import calculo as c
from apps.tablero import grafica, presentacion

D = Decimal
M1, M2, M3, M4 = c.DEFINICIONES


class MotivoTests(TestCase):
    def resultado(self, definicion, valor):
        return c.ResultadoMetrica(definicion, valor, c.semaforo(definicion, valor), 0, D(0))

    def test_verde_no_tiene_motivo(self):
        self.assertEqual(c.motivo(self.resultado(M1, D("95"))), "")

    def test_amarillo_cita_el_umbral_del_verde(self):
        self.assertEqual(
            c.motivo(self.resultado(M1, D("90"))), "Amarillo: 90.0 % es menor que 95 %."
        )
        self.assertEqual(c.motivo(self.resultado(M4, D("3.5"))), "Amarillo: 3.5 supera 2.")

    def test_rojo_cita_el_umbral_del_amarillo(self):
        self.assertEqual(c.motivo(self.resultado(M2, D("50"))), "Rojo: 50.0 % es menor que 85 %.")
        self.assertEqual(c.motivo(self.resultado(M4, D("7"))), "Rojo: 7.0 supera 5.")

    def test_sin_datos_no_tiene_motivo(self):
        self.assertEqual(c.motivo(c.ResultadoMetrica(M1, None, None, None, None)), "")


class MedidaFaltanteTests(TestCase):
    def test_indica_cual_medida_falta(self):
        medidas = c.Medidas(funciones_entregadas=3)
        self.assertEqual(
            c.medida_faltante(M1, medidas), "Falta registrar las funciones requeridas del periodo."
        )

    def test_denominador_cero(self):
        medidas = c.Medidas(funciones_entregadas=0, funciones_requeridas=0)
        self.assertIn("es 0", c.medida_faltante(M1, medidas))

    def test_sin_faltante(self):
        medidas = c.Medidas(funciones_entregadas=3, funciones_requeridas=4)
        self.assertEqual(c.medida_faltante(M1, medidas), "")


class MensajeEstadoTests(TestCase):
    def test_en_riesgo_con_amarillas(self):
        salud = c.evaluar(c.Medidas(10, 9, 25, 24, 20, 17, 7, D("2")))
        self.assertEqual(
            presentacion.mensaje_estado(salud),
            "Índice 72.0: entre 70 y menos de 85. Atiende primero las métricas en amarillo.",
        )

    def test_saludable_todo_verde(self):
        salud = c.evaluar(c.Medidas(10, 10, 20, 20, 20, 20, 2, D("1")))
        self.assertEqual(
            presentacion.mensaje_estado(salud), "Índice 100.0: las cuatro métricas están en verde."
        )

    def test_critico_pide_atender_las_rojas(self):
        salud = c.evaluar(c.Medidas(10, 5, 20, 5, 20, 5, 50, D("1")))
        self.assertEqual(salud.estado, c.CRITICO)
        self.assertIn("menor que 70", presentacion.mensaje_estado(salud))
        self.assertIn("en rojo", presentacion.mensaje_estado(salud))

    def test_sin_evaluar(self):
        self.assertIn("No se calculó el índice", presentacion.mensaje_estado(c.evaluar(c.Medidas())))

    def test_r18_cita_la_metrica_en_rojo(self):
        salud = c.Salud(
            (c.ResultadoMetrica(M4, D("7"), c.ROJO, 0, D(0)),), D("90"), c.EN_RIESGO, True
        )
        self.assertEqual(
            presentacion.mensaje_estado(salud),
            "El índice es saludable, pero densidad de defectos está en rojo. "
            "El estado se limita a «En riesgo»; se conserva el índice (90.0).",
        )


class FilaYReglasTests(TestCase):
    def test_fila_de_metrica_con_datos(self):
        medidas = c.Medidas(10, 9, 25, 24, 20, 17, 7, D("2"))
        fila = presentacion.fila_metrica(c.evaluar(medidas).metricas[0], medidas)
        self.assertEqual(
            (fila["codigo"], fila["valor"], fila["unidad_texto"], fila["nombre_semaforo"]),
            ("M1", "90.0", "%", "Amarillo"),
        )
        self.assertEqual(fila["aporte_texto"], "60 pts × 25 % = 15.0 al índice")

    def test_fila_de_densidad_usa_su_unidad(self):
        medidas = c.Medidas(10, 9, 25, 24, 20, 17, 7, D("2"))
        fila = presentacion.fila_metrica(c.evaluar(medidas).metricas[3], medidas)
        self.assertEqual((fila["valor"], fila["unidad_texto"]), ("3.5", "defectos/KLOC"))

    def test_fila_sin_datos_explica_que_falta(self):
        medidas = c.Medidas()
        fila = presentacion.fila_metrica(c.evaluar(medidas).metricas[0], medidas)
        self.assertTrue(fila["sin_datos"])
        self.assertEqual(fila["semaforo"], "sin-datos")
        self.assertTrue(fila["faltante"].startswith("Falta registrar"))

    def test_tabla_de_reglas(self):
        filas = {f["codigo"]: f for f in presentacion.reglas()}
        self.assertEqual(
            (filas["M1"]["verde"], filas["M1"]["amarillo"], filas["M1"]["rojo"]),
            ("≥ 95 %", "80 – < 95 %", "< 80 %"),
        )
        self.assertEqual(
            (filas["M4"]["verde"], filas["M4"]["amarillo"], filas["M4"]["rojo"]),
            ("≤ 2", "> 2 – 5", "> 5"),
        )
        self.assertEqual(presentacion.pesos_texto(), "25 %, 30 %, 20 %, 25 %")


class GraficaTests(TestCase):
    def test_un_punto_por_periodo_coloreado(self):
        datos = grafica.construir(M1, [("E1", D("100")), ("E2", D("90"))])
        self.assertEqual([p["semaforo"] for p in datos["puntos"]], ["verde", "amarillo"])
        self.assertEqual([p["texto"] for p in datos["puntos"]], ["100.0", "90.0"])
        self.assertEqual(len(datos["segmentos"]), 1)

    def test_periodo_sin_datos_no_lleva_punto_ni_une_la_linea(self):
        datos = grafica.construir(M1, [("E1", D("100")), ("E2", None), ("E3", D("90"))])
        self.assertTrue(datos["puntos"][1]["sin_datos"])
        self.assertNotIn("y", datos["puntos"][1])
        self.assertEqual(datos["segmentos"], [])
        self.assertEqual(datos["periodos_sin_datos"], ["E2"])

    def test_un_solo_periodo_queda_al_centro(self):
        datos = grafica.construir(M1, [("E1", D("90"))])
        self.assertEqual(len(datos["puntos"]), 1)
        centro = grafica.IZQ + (grafica.ANCHO - grafica.IZQ - grafica.DER) / 2
        self.assertEqual(datos["puntos"][0]["x"], centro)

    def test_el_eje_incluye_los_cortes_de_la_metrica(self):
        textos = [e["texto"] for e in grafica.construir(M1, [("E1", D("90"))])["ejes"]]
        self.assertIn("95", textos)
        self.assertIn("80", textos)
        textos = [e["texto"] for e in grafica.construir(M4, [("E1", D("3.5"))])["ejes"]]
        self.assertIn("2", textos)
        self.assertIn("5", textos)

    def test_un_valor_bajo_amplia_el_eje_hacia_abajo(self):
        datos = grafica.construir(M1, [("E1", D("35"))])
        self.assertEqual(datos["ejes"][0]["texto"], "30")

    def test_densidad_muy_alta_amplia_el_eje_hacia_arriba(self):
        datos = grafica.construir(M4, [("E1", D("9.2"))])
        self.assertEqual(datos["ejes"][-1]["texto"], "11")

    def test_valor_mas_alto_queda_mas_arriba(self):
        datos = grafica.construir(M1, [("E1", D("100")), ("E2", D("70"))])
        self.assertLess(datos["puntos"][0]["y"], datos["puntos"][1]["y"])
