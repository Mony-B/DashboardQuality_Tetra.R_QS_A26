"""Pruebas del CU 03 · Planear y dar seguimiento a las actividades SQA (R8, R9, R21, R32)."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.actividades.models import Actividad
from apps.proyectos.models import Periodo, Proyecto

Usuario = get_user_model()
CLAVE = "Clave-segura-123"
ENLACE = "https://drive.google.com/drive/folders/evidencia-cu01"

DATOS = {
    "tecnica": "revision_pares",
    "artefacto": "CU 01",
    "responsable": "Integrante 2",
    "fecha": "2026-12-16",
}


class BaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", CLAVE)
        cls.beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        cls.proyecto = Proyecto.objects.create(
            usuario=cls.ana, nombre="QuaQlity", marco_trabajo="Kanban"
        )
        cls.periodo = Periodo.objects.create(
            proyecto=cls.proyecto,
            nombre="Entrega 1",
            fecha_inicio=date(2026, 12, 12),
            fecha_fin=date(2026, 12, 24),
        )
        cls.url_lista = reverse("actividades:lista", args=[cls.periodo.pk])
        cls.url_nueva = reverse("actividades:nueva", args=[cls.periodo.pk])

    def setUp(self):
        self.client.force_login(self.ana)

    def crear(self, **cambios):
        datos = {
            "periodo": self.periodo,
            "tecnica": Actividad.Tecnica.REVISION_PERSONAL,
            "artefacto": "CU 01",
            "responsable": "Integrante 1",
            "fecha": date(2026, 12, 14),
            **cambios,
        }
        return Actividad.objects.create(**datos)

    def planear(self, **cambios):
        return self.client.post(self.url_nueva, {**DATOS, **cambios})


class PantallaTests(BaseTests):
    """Pasos 1 y 2, FA-5."""

    def test_muestra_el_formulario_con_el_catalogo_de_seis_tecnicas(self):
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Planear una actividad")
        for tecnica in (
            "Revisión personal",
            "Revisión entre pares",
            "Análisis estático",
            "Prueba unitaria",
            "Prueba de integración",
            "Prueba de seguridad",
        ):
            self.assertContains(respuesta, tecnica)
        self.assertContains(respuesta, "Planear actividad")
        self.assertContains(respuesta, "Cancelar")

    def test_periodo_sin_actividades_lo_indica_en_lugar_de_la_tabla(self):
        respuesta = self.client.get(self.url_lista)
        self.assertContains(
            respuesta,
            "Este periodo todavía no tiene actividades. Planea la primera con el formulario "
            "de arriba.",
        )
        self.assertNotContains(respuesta, "<table")

    def test_con_actividades_muestra_la_tabla_con_estado_y_enlace(self):
        self.crear(enlace_evidencia=ENLACE, estado=Actividad.Estado.COMPLETADA)
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, "<table")
        self.assertContains(respuesta, "Revisión personal")
        self.assertContains(respuesta, "14/12/2026")
        self.assertContains(respuesta, ENLACE)
        self.assertContains(respuesta, '<option value="completada" selected>')

    def test_solo_muestra_las_actividades_del_periodo(self):
        otro = Periodo.objects.create(
            proyecto=self.proyecto,
            nombre="Entrega 2",
            fecha_inicio=date(2026, 12, 25),
            fecha_fin=date(2027, 1, 7),
        )
        self.crear(artefacto="Solo de la entrega 1")
        self.crear(periodo=otro, artefacto="Solo de la entrega 2")
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, "Solo de la entrega 1")
        self.assertNotContains(respuesta, "Solo de la entrega 2")

    def test_el_texto_capturado_se_escapa(self):
        self.crear(artefacto="<script>alert(1)</script>")
        respuesta = self.client.get(self.url_lista)
        self.assertNotContains(respuesta, "<script>alert(1)</script>")
        self.assertContains(respuesta, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_avisa_antes_de_planear_que_la_actividad_no_se_podra_editar(self):
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, "no se podrá editar ni eliminar")
        self.assertContains(respuesta, "Sí, planear")
        self.assertContains(respuesta, "Revisar datos")

    def test_no_existe_edicion_de_actividades(self):
        actividad = self.crear()
        self.assertNotContains(self.client.get(self.url_lista), "Editar")
        self.assertEqual(
            self.client.post(f"/actividades/{actividad.pk}/editar/", DATOS).status_code, 404
        )

    def test_el_menu_abre_el_periodo_actual(self):
        self.assertRedirects(self.client.get(reverse("actividades:inicio")), self.url_lista)

    def test_el_menu_sin_proyectos_regresa_a_mis_proyectos(self):
        self.client.force_login(self.beto)
        respuesta = self.client.get(reverse("actividades:inicio"))
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))


class PlanearTests(BaseTests):
    """Pasos 3 a 7, FA-1 (R8)."""

    def test_planea_la_actividad_en_estado_planeada(self):
        respuesta = self.planear()
        self.assertRedirects(respuesta, self.url_lista)
        actividad = Actividad.objects.get()
        self.assertEqual(actividad.periodo, self.periodo)
        self.assertEqual(actividad.tecnica, "revision_pares")
        self.assertEqual(actividad.artefacto, "CU 01")
        self.assertEqual(actividad.responsable, "Integrante 2")
        self.assertEqual(actividad.fecha, date(2026, 12, 16))
        self.assertEqual(actividad.estado, "planeada")
        self.assertEqual(actividad.enlace_evidencia, "")

    def test_muestra_el_mensaje_de_confirmacion_y_la_actividad_en_la_tabla(self):
        respuesta = self.client.get(self.planear().url)
        self.assertContains(respuesta, "Actividad planeada con estado «planeada».")
        self.assertContains(respuesta, "Revisión entre pares")

    def test_acepta_cada_tecnica_del_catalogo(self):
        for valor, _ in Actividad.Tecnica.choices:
            self.planear(tecnica=valor)
        self.assertEqual(Actividad.objects.count(), 6)

    def test_se_permiten_actividades_repetidas(self):
        self.planear()
        self.planear()
        self.assertEqual(Actividad.objects.count(), 2)

    def test_la_fecha_es_libre_aunque_este_fuera_del_periodo(self):
        self.planear(fecha="2030-01-01")
        self.assertEqual(Actividad.objects.get().fecha, date(2030, 1, 1))

    def test_las_cuatro_validaciones_de_campo_vacio_juntas(self):
        respuesta = self.client.post(
            self.url_nueva, {"tecnica": "", "artefacto": "", "responsable": "", "fecha": ""}
        )
        self.assertEqual(respuesta.status_code, 200)
        for mensaje in (
            "Elige una técnica.",
            "Escribe el artefacto o caso de uso.",
            "Escribe el responsable.",
            "Elige la fecha.",
        ):
            self.assertContains(respuesta, mensaje)
        self.assertEqual(Actividad.objects.count(), 0)

    def test_un_solo_campo_vacio_conserva_los_demas(self):
        respuesta = self.planear(responsable="")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(list(respuesta.context["form"].errors), ["responsable"])
        self.assertContains(respuesta, 'value="CU 01"')
        self.assertContains(respuesta, "Escribe el responsable.")
        self.assertEqual(Actividad.objects.count(), 0)

    def test_espacios_en_blanco_cuentan_como_vacio(self):
        respuesta = self.planear(artefacto="   ")
        self.assertContains(respuesta, "Escribe el artefacto o caso de uso.")

    def test_tecnica_fuera_del_catalogo_se_rechaza(self):
        respuesta = self.planear(tecnica="adivinanza")
        self.assertContains(respuesta, "Elige una técnica.")
        self.assertEqual(Actividad.objects.count(), 0)

    def test_longitudes_maximas(self):
        respuesta = self.planear(artefacto="x" * 121, responsable="y" * 81)
        self.assertEqual(set(respuesta.context["form"].errors), {"artefacto", "responsable"})
        self.assertEqual(Actividad.objects.count(), 0)
        self.planear(artefacto="x" * 120, responsable="y" * 80)
        self.assertEqual(Actividad.objects.count(), 1)

    def test_fecha_invalida(self):
        respuesta = self.planear(fecha="31/02/2026")
        self.assertContains(respuesta, "Elige una fecha válida.")


class EstadoTests(BaseTests):
    """Pasos 8 y 9, FA-4."""

    def cambiar(self, actividad, estado):
        return self.client.post(
            reverse("actividades:estado", args=[actividad.pk]), {"estado": estado}
        )

    def test_cambia_a_en_curso_y_muestra_el_mensaje(self):
        actividad = self.crear()
        respuesta = self.cambiar(actividad, "en_curso")
        self.assertRedirects(respuesta, self.url_lista, fetch_redirect_response=False)
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "en_curso")
        self.assertContains(self.client.get(self.url_lista), "Estado actualizado a «en curso».")

    def test_cambia_a_completada(self):
        actividad = self.crear()
        self.cambiar(actividad, "completada")
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "completada")
        self.assertContains(self.client.get(self.url_lista), "Estado actualizado a «completada».")

    def test_puede_cambiar_hacia_atras_y_conserva_el_enlace(self):
        actividad = self.crear(estado="completada", enlace_evidencia=ENLACE)
        self.cambiar(actividad, "en_curso")
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "en_curso")
        self.assertEqual(actividad.enlace_evidencia, ENLACE)

    def test_estado_invalido_no_cambia_nada(self):
        actividad = self.crear()
        respuesta = self.cambiar(actividad, "terminada")
        self.assertRedirects(respuesta, self.url_lista, fetch_redirect_response=False)
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "planeada")
        self.assertContains(self.client.get(self.url_lista), "Elige un estado válido.")


class EnlaceTests(BaseTests):
    """Pasos 10 a 13, FA-2 y FA-3 (R9, R32)."""

    def guardar(self, actividad, enlace):
        return self.client.post(
            reverse("actividades:enlace", args=[actividad.pk]), {"enlace": enlace}
        )

    def test_guarda_un_enlace_https_y_muestra_el_mensaje(self):
        actividad = self.crear()
        respuesta = self.guardar(actividad, ENLACE)
        self.assertRedirects(respuesta, self.url_lista, fetch_redirect_response=False)
        actividad.refresh_from_db()
        self.assertEqual(actividad.enlace_evidencia, ENLACE)
        self.assertContains(self.client.get(self.url_lista), "Enlace de evidencia guardado.")

    def test_acepta_http(self):
        actividad = self.crear()
        self.guardar(actividad, "http://servidor.local/reporte")
        actividad.refresh_from_db()
        self.assertEqual(actividad.enlace_evidencia, "http://servidor.local/reporte")

    def test_reemplaza_un_enlace_anterior(self):
        actividad = self.crear(enlace_evidencia=ENLACE)
        self.guardar(actividad, "https://drive.google.com/otro")
        actividad.refresh_from_db()
        self.assertEqual(actividad.enlace_evidencia, "https://drive.google.com/otro")

    def test_guardar_el_enlace_no_cambia_el_estado(self):
        actividad = self.crear(estado="en_curso")
        self.guardar(actividad, ENLACE)
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "en_curso")

    def test_enlaces_invalidos_no_se_guardan_y_conservan_el_anterior(self):
        actividad = self.crear(enlace_evidencia=ENLACE)
        for invalido in (
            "evidencia final",
            "reporte-bandit",
            "ftp://servidor/reporte",
            "javascript:alert(1)",
            "https://",
        ):
            with self.subTest(invalido=invalido):
                respuesta = self.guardar(actividad, invalido)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(
                    respuesta, "Escribe un enlace válido que empiece con http:// o https://."
                )
                actividad.refresh_from_db()
                self.assertEqual(actividad.enlace_evidencia, ENLACE)

    def test_el_error_sale_en_la_fila_de_la_actividad_con_lo_escrito(self):
        primera = self.crear(artefacto="Primera")
        segunda = self.crear(artefacto="Segunda")
        respuesta = self.guardar(segunda, "reporte-bandit")
        self.assertContains(respuesta, 'value="reporte-bandit"')
        self.assertContains(respuesta, "Escribe un enlace válido", count=1)
        self.assertEqual(respuesta.context["error_enlace"][0], segunda.pk)
        self.assertNotEqual(respuesta.context["error_enlace"][0], primera.pk)

    def test_campo_vacio_quita_el_enlace_y_conserva_el_estado(self):
        actividad = self.crear(estado="completada", enlace_evidencia=ENLACE)
        respuesta = self.guardar(actividad, "")
        self.assertRedirects(respuesta, self.url_lista, fetch_redirect_response=False)
        actividad.refresh_from_db()
        self.assertEqual(actividad.enlace_evidencia, "")
        self.assertEqual(actividad.estado, "completada")
        self.assertContains(self.client.get(self.url_lista), "Enlace de evidencia quitado.")

    def test_enlace_demasiado_largo(self):
        actividad = self.crear()
        respuesta = self.guardar(actividad, "https://ejemplo.com/" + "a" * 500)
        self.assertEqual(respuesta.status_code, 200)
        actividad.refresh_from_db()
        self.assertEqual(actividad.enlace_evidencia, "")

    def test_no_existe_carga_de_archivos(self):
        """R32: solo se guarda el enlace, nunca un archivo."""
        self.assertNotIn("FileField", [type(c).__name__ for c in Actividad._meta.get_fields()])


class AccesoTests(BaseTests):
    """R20 y R21: sin sesión se pide iniciar sesión; lo ajeno responde 404."""

    def setUp(self):
        super().setUp()
        self.actividad = self.crear()

    def urls(self):
        return {
            "lista": self.url_lista,
            "nueva": self.url_nueva,
            "estado": reverse("actividades:estado", args=[self.actividad.pk]),
            "enlace": reverse("actividades:enlace", args=[self.actividad.pk]),
        }

    def test_sin_sesion_pide_iniciar_sesion(self):
        self.client.logout()
        for nombre, url in self.urls().items():
            with self.subTest(nombre=nombre):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(reverse("cuentas:iniciar_sesion"), respuesta.url)

    def test_periodo_ajeno_responde_404_al_ver_y_al_planear(self):
        self.client.force_login(self.beto)
        self.assertEqual(self.client.get(self.url_lista).status_code, 404)
        self.assertEqual(self.planear().status_code, 404)
        self.assertEqual(Actividad.objects.count(), 1)

    def test_actividad_ajena_responde_404_al_cambiar_estado_y_enlace(self):
        self.client.force_login(self.beto)
        urls = self.urls()
        self.assertEqual(
            self.client.post(urls["estado"], {"estado": "completada"}).status_code, 404
        )
        self.assertEqual(self.client.post(urls["enlace"], {"enlace": ENLACE}).status_code, 404)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.estado, "planeada")
        self.assertEqual(self.actividad.enlace_evidencia, "")

    def test_las_acciones_solo_aceptan_post(self):
        urls = self.urls()
        for nombre in ("nueva", "estado", "enlace"):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(urls[nombre]).status_code, 405)

    def test_los_formularios_llevan_proteccion_csrf(self):
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, "csrfmiddlewaretoken", count=4)


class ModeloTests(BaseTests):
    def test_estado_inicial_es_planeada(self):
        self.assertEqual(self.crear().estado, Actividad.Estado.PLANEADA)

    def test_get_absolute_url_vuelve_a_la_lista_del_periodo(self):
        self.assertEqual(self.crear().get_absolute_url(), self.url_lista)

    def test_al_borrar_el_periodo_se_borran_sus_actividades(self):
        self.crear()
        self.periodo.delete()
        self.assertEqual(Actividad.objects.count(), 0)
