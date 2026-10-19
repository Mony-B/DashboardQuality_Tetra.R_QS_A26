"""Pruebas de las restricciones de los modelos del CU 01 (la base de datos también las cuida)."""

from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()


class RestriccionesTests(TestCase):
    def setUp(self):
        ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", "Clave-segura-123")
        self.proyecto = Proyecto.objects.create(usuario=ana, nombre="P1", marco_trabajo="Kanban")

    def test_bd_rechaza_fin_antes_de_inicio(self):
        with self.assertRaises(IntegrityError):
            Periodo.objects.create(
                proyecto=self.proyecto,
                nombre="X",
                fecha_inicio=date(2026, 12, 24),
                fecha_fin=date(2026, 12, 12),
            )

    def test_bd_rechaza_proyecto_repetido_del_mismo_usuario(self):
        with self.assertRaises(IntegrityError):
            Proyecto.objects.create(
                usuario=self.proyecto.usuario, nombre="P1", marco_trabajo="Scrum"
            )

    def test_traslapes_excluye_al_propio_periodo(self):
        periodo = Periodo.objects.create(
            proyecto=self.proyecto,
            nombre="E1",
            fecha_inicio=date(2026, 12, 1),
            fecha_fin=date(2026, 12, 10),
        )
        self.assertFalse(periodo.traslapes().exists())
