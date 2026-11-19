"""Pruebas del cálculo de salud (CU 04). No necesitan base de datos."""

from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase

from apps.tablero import calculo as c

D = Decimal


def medidas(req=10, ent=10, ejec=100, apro=100, verif=20, con_prueba=20, defectos=2, kloc="1"):
    return c.Medidas(req, ent, ejec, apro, verif, con_prueba, defectos, D(kloc))


def definicion(clave):
    return next(d for d in c.DEFINICIONES if d.clave == clave)


class FormulasTests(TestCase):
    def test_valores_de_las_cuatro_metricas(self):
        v = c.valores(c.Medidas(10, 9, 25, 24, 20, 17, 7, D("2")))
        self.assertEqual(v["capacidad_funcional"], D("90"))
        self.assertEqual(v["tasa_aprobacion"], D("96"))
        self.assertEqual(v["cobertura_requisitos"], D("85"))
        self.assertEqual(v["densidad_defectos"], D("3.5"))

    def test_sin_medida_o_divisor_cero_no_hay_dato(self):
        self.assertIsNone(c.valores(c.Medidas())["capacidad_funcional"])
        self.assertIsNone(c.valores(medidas(req=0, ent=0))["capacidad_funcional"])
        self.assertIsNone(c.valores(medidas(ejec=0, apro=0))["tasa_aprobacion"])
        self.assertIsNone(c.valores(medidas(verif=0, con_prueba=0))["cobertura_requisitos"])
        self.assertIsNone(c.valores(medidas(kloc="0"))["densidad_defectos"])

    def test_cero_aprobados_es_un_dato_valido(self):
        self.assertEqual(c.valores(medidas(apro=0))["tasa_aprobacion"], D("0"))

    def test_de_periodo_toma_los_ocho_campos(self):
        periodo = SimpleNamespace(
            funciones_requeridas=1, funciones_entregadas=1, casos_ejecutados=2,
            casos_aprobados=2, requisitos_verificables=3, requisitos_con_prueba=3,
            defectos_codigo=0, kloc=D("1.5"), otro_campo="ignorado",
        )  # fmt: skip
        self.assertEqual(c.Medidas.de_periodo(periodo), c.Medidas(1, 1, 2, 2, 3, 3, 0, D("1.5")))


class SemaforoTests(TestCase):
    def test_bordes_capacidad_funcional_y_cobertura(self):
        for clave in ("capacidad_funcional", "cobertura_requisitos"):
            d = definicion(clave)
            self.assertEqual(c.semaforo(d, D("95")), c.VERDE)
            self.assertEqual(c.semaforo(d, D("94.99")), c.AMARILLO)
            self.assertEqual(c.semaforo(d, D("80")), c.AMARILLO)
            self.assertEqual(c.semaforo(d, D("79.99")), c.ROJO)

    def test_bordes_tasa_de_aprobacion(self):
        d = definicion("tasa_aprobacion")
        self.assertEqual(c.semaforo(d, D("95")), c.VERDE)
        self.assertEqual(c.semaforo(d, D("94.99")), c.AMARILLO)
        self.assertEqual(c.semaforo(d, D("85")), c.AMARILLO)
        self.assertEqual(c.semaforo(d, D("84.99")), c.ROJO)

    def test_bordes_densidad_de_defectos(self):
        d = definicion("densidad_defectos")
        self.assertEqual(c.semaforo(d, D("0")), c.VERDE)
        self.assertEqual(c.semaforo(d, D("2")), c.VERDE)
        self.assertEqual(c.semaforo(d, D("2.01")), c.AMARILLO)
        self.assertEqual(c.semaforo(d, D("5")), c.AMARILLO)
        self.assertEqual(c.semaforo(d, D("5.01")), c.ROJO)


class IndiceYEstadoTests(TestCase):
    def test_pesos_suman_cien(self):
        self.assertEqual(sum(d.peso for d in c.DEFINICIONES), 100)

    def test_todo_en_verde_da_100_y_saludable(self):
        salud = c.evaluar(medidas())
        self.assertEqual(salud.indice, D("100"))
        self.assertEqual(salud.estado, c.SALUDABLE)
        self.assertFalse(salud.limitado_por_rojo)

    def test_ejemplo_del_wireframe_72_en_riesgo(self):
        salud = c.evaluar(c.Medidas(10, 9, 25, 24, 20, 17, 7, D("2")))
        self.assertEqual(salud.indice, D("72"))
        self.assertEqual(salud.estado, c.EN_RIESGO)
        aportes = {r.clave: r.aporte for r in salud.metricas}
        self.assertEqual(
            aportes,
            {
                "capacidad_funcional": D("15"),
                "tasa_aprobacion": D("30"),
                "cobertura_requisitos": D("12"),
                "densidad_defectos": D("15"),
            },
        )

    def test_bordes_del_estado_por_indice(self):
        self.assertEqual(c.estado_por_indice(D("85")), c.SALUDABLE)
        self.assertEqual(c.estado_por_indice(D("84.9")), c.EN_RIESGO)
        self.assertEqual(c.estado_por_indice(D("70")), c.EN_RIESGO)
        self.assertEqual(c.estado_por_indice(D("69.9")), c.CRITICO)

    def test_critico_con_metricas_en_rojo(self):
        # M1 80/100 amarillo (15) + M2 rojo (0) + M3 rojo (0) + M4 rojo (0) = 15
        salud = c.evaluar(medidas(ent=8, apro=50, con_prueba=10, defectos=10))
        self.assertEqual(salud.estado, c.CRITICO)
        self.assertLess(salud.indice, D("70"))

    def test_una_metrica_en_rojo_cuesta_cero_puntos(self):
        salud = c.evaluar(medidas(defectos=6))  # M4 = 6 → rojo
        m4 = next(r for r in salud.metricas if r.clave == "densidad_defectos")
        self.assertEqual((m4.semaforo, m4.puntos, m4.aporte), (c.ROJO, 0, D("0")))
        self.assertEqual(salud.indice, D("75"))
        self.assertEqual(salud.estado, c.EN_RIESGO)

    def test_r18_con_los_pesos_actuales_no_se_alcanza(self):
        # El mejor índice posible con una métrica en rojo es 75 (la de menor peso en 0):
        # nunca llega a 85, así que la regla R18 hoy no se activa.
        mejor = max(100 - d.peso for d in c.DEFINICIONES)
        self.assertLess(mejor, 85)

    def test_r18_limita_saludable_a_en_riesgo_si_hay_una_metrica_en_rojo(self):
        d = c.DEFINICIONES[0]
        rojo = c.ResultadoMetrica(d, D("10"), c.ROJO, 0, D("0"))
        verde = c.ResultadoMetrica(d, D("100"), c.VERDE, 100, D("25"))
        self.assertEqual(c.limitar_por_rojo(c.SALUDABLE, [verde, rojo]), c.EN_RIESGO)
        self.assertEqual(c.limitar_por_rojo(c.SALUDABLE, [verde, verde]), c.SALUDABLE)
        self.assertEqual(c.limitar_por_rojo(c.CRITICO, [verde, rojo]), c.CRITICO)
        self.assertEqual(c.limitar_por_rojo(c.EN_RIESGO, [verde, rojo]), c.EN_RIESGO)


class SinDatosTests(TestCase):
    def test_sin_medidas_es_sin_evaluar(self):
        salud = c.evaluar(c.Medidas())
        self.assertEqual(salud.estado, c.SIN_EVALUAR)
        self.assertIsNone(salud.indice)
        self.assertTrue(all(r.sin_datos for r in salud.metricas))

    def test_una_metrica_sin_datos_deja_todo_sin_evaluar(self):
        salud = c.evaluar(medidas(kloc="0"))
        self.assertEqual(salud.estado, c.SIN_EVALUAR)
        self.assertIsNone(salud.indice)
        sin_datos = [r.clave for r in salud.metricas if r.sin_datos]
        self.assertEqual(sin_datos, ["densidad_defectos"])
        # Las demás conservan su valor y semáforo.
        self.assertEqual(salud.metricas[0].semaforo, c.VERDE)


class RedondeoTests(TestCase):
    def test_redondea_a_un_decimal_mitad_hacia_arriba(self):
        self.assertEqual(c.redondear(D("72.25")), D("72.3"))
        self.assertEqual(c.redondear(D("3.5")), D("3.5"))
        self.assertIsNone(c.redondear(None))

    def test_el_semaforo_usa_el_valor_exacto_no_el_mostrado(self):
        # 94.96 se muestra como 95.0 pero sigue siendo amarillo.
        d = definicion("capacidad_funcional")
        self.assertEqual(c.redondear(D("94.96")), D("95.0"))
        self.assertEqual(c.semaforo(d, D("94.96")), c.AMARILLO)
