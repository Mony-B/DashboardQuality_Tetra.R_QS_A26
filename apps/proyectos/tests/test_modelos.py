from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()


class ModelosTests(TestCase):
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

    def test_no_se_repite_el_nombre_de_proyecto_para_el_mismo_usuario(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Proyecto.objects.create(usuario=self.ana, nombre="Dashboard SQA", marco_trabajo="X")

    def test_no_se_repite_el_nombre_de_periodo_en_el_proyecto(self):
        self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_periodo("Entrega 1", date(2027, 1, 1), date(2027, 1, 7))

    def test_la_base_rechaza_un_kloc_menor_o_igual_a_cero(self):
        periodo = self.crear_periodo("Entrega 1", date(2026, 12, 12), date(2026, 12, 24))
        periodo.kloc = Decimal("0")
        with self.assertRaises(IntegrityError), transaction.atomic():
            periodo.save()


class MisProyectosTests(TestCase):
    def test_solo_muestra_los_proyectos_del_usuario(self):
        ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", "Clave-segura-123")
        Proyecto.objects.create(usuario=ana, nombre="De Ana", marco_trabajo="Kanban")
        Proyecto.objects.create(usuario=beto, nombre="De Beto", marco_trabajo="Scrum")
        self.client.force_login(ana)
        respuesta = self.client.get(reverse("proyectos:mis_proyectos"))
        self.assertContains(respuesta, "De Ana")
        self.assertNotContains(respuesta, "De Beto")

    def test_sin_sesion_pide_iniciar_sesion(self):
        respuesta = self.client.get(reverse("proyectos:mis_proyectos"))
        self.assertEqual(respuesta.status_code, 302)
