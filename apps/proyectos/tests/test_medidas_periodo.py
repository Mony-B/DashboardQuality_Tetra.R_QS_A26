from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()


class MedidasPeriodoModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        cls.proyecto = Proyecto.objects.create(
            usuario=cls.ana, nombre="Dashboard SQA", marco_trabajo="Kanban"
        )

    def crear_periodo(self, nombre, inicio, fin):
        return Periodo.objects.create(
            proyecto=self.proyecto, nombre=nombre, fecha_inicio=inicio, fecha_fin=fin
        )

    def test_get_absolute_url_medidas_usa_la_url_del_diseno(self):
        periodo = self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        self.assertEqual(
            periodo.get_absolute_url_medidas(),
            f"/proyectos/{self.proyecto.pk}/periodos/{periodo.pk}/medidas/",
        )

    def test_periodo_actual_es_el_de_inicio_mas_reciente(self):
        self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        reciente = self.crear_periodo("Entrega 2", date(2026, 12, 25), date(2027, 1, 7))
        self.assertEqual(self.proyecto.periodo_actual, reciente)

    def test_etiqueta_del_periodo(self):
        periodo = self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        self.assertEqual(periodo.etiqueta, "Entrega 1 (12/12/2026 – 24/12/2026)")

    def test_tiene_medidas_distingue_vacio_de_cero(self):
        periodo = self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        self.assertFalse(periodo.tiene_medidas())
        periodo.casos_aprobados = 0
        self.assertTrue(periodo.tiene_medidas())

    def test_la_base_rechaza_un_kloc_menor_o_igual_a_cero(self):
        periodo = self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        periodo.kloc = Decimal("0")
        with self.assertRaises(IntegrityError), transaction.atomic():
            periodo.save()
