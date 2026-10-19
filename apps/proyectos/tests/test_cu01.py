"""Pruebas del CU 01 · Iniciar el monitoreo de un proyecto (R2, R3, R4, R21, R23).

Cada clase corresponde a un flujo de la especificación del CU 01.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.proyectos.metricas import METRICAS
from apps.proyectos.models import MetaProyecto, Periodo, Proyecto

Usuario = get_user_model()
CLAVE = "Clave-segura-123"
URL_MIS_PROYECTOS = reverse("proyectos:mis_proyectos")
URL_NUEVO = reverse("proyectos:nuevo")


def datos_proyecto(**cambios):
    datos = {
        "nombre": "Dashboard SQA",
        "marco_trabajo": "Kanban",
        "descripcion": "",
        "nombre_periodo": "Entrega 1",
        "fecha_inicio": "2026-12-12",
        "fecha_fin": "2026-12-24",
    }
    datos.update(cambios)
    return datos


def datos_periodo(**cambios):
    datos = {"nombre_periodo": "Entrega 2", "fecha_inicio": "2026-12-25", "fecha_fin": "2027-01-07"}
    datos.update(cambios)
    return datos


class BaseCU01(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("ana", "ana@ejemplo.com", CLAVE)
        self.client.force_login(self.ana)

    def crear_proyecto(
        self, usuario=None, nombre="Dashboard SQA", periodos=(("Entrega 1", 12, 24),)
    ):
        proyecto = Proyecto.objects.create(
            usuario=usuario or self.ana, nombre=nombre, marco_trabajo="Kanban"
        )
        proyecto.crear_metas_sugeridas()
        for nombre_periodo, inicio, fin in periodos:
            Periodo.objects.create(
                proyecto=proyecto,
                nombre=nombre_periodo,
                fecha_inicio=date(2026, 12, inicio),
                fecha_fin=date(2026, 12, fin),
            )
        return proyecto

    def errores(self, respuesta, campo):
        return respuesta.context["form"].errors.get(campo, [])


class FlujoNormalTests(BaseCU01):
    """Pasos 1 a 8 del flujo normal y postcondiciones de éxito."""

    def test_formulario_vacio_se_muestra(self):
        respuesta = self.client.get(URL_NUEVO)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Guardar y capturar medidas")
        self.assertContains(respuesta, 'maxlength="100"')
        self.assertContains(respuesta, 'type="date"')

    def test_registrar_proyecto_crea_proyecto_metas_y_periodo(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto())

        proyecto = Proyecto.objects.get()
        periodo = proyecto.periodos.get()
        self.assertRedirects(respuesta, reverse("medidas:captura", args=[periodo.pk]))
        self.assertEqual(proyecto.usuario, self.ana)
        self.assertEqual((periodo.nombre, periodo.fecha_inicio), ("Entrega 1", date(2026, 12, 12)))
        self.assertEqual(proyecto.periodo_actual, periodo)

    def test_metas_sugeridas_al_crear(self):
        """R2: 100 %, ≥ 95 %, 100 %, 100 %, 100 %."""
        self.client.post(URL_NUEVO, datos_proyecto())
        metas = dict(MetaProyecto.objects.values_list("metrica", "valor"))
        self.assertEqual(metas, {m.clave: m.meta_sugerida for m in METRICAS})
        self.assertEqual(sorted(metas.values()), [95, 100, 100, 100, 100])

    def test_descripcion_es_opcional_y_se_guarda(self):
        self.client.post(URL_NUEVO, datos_proyecto(descripcion="Proyecto de la materia"))
        self.assertEqual(Proyecto.objects.get().descripcion, "Proyecto de la materia")

    def test_mensaje_de_exito_en_captura_de_medidas(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(), follow=True)
        self.assertContains(
            respuesta, "Proyecto registrado. Dashboard SQA quedó con el periodo Entrega 1"
        )
        self.assertContains(respuesta, "Captura de medidas")

    def test_marco_y_periodo_son_texto_libre(self):
        self.client.post(
            URL_NUEVO, datos_proyecto(marco_trabajo="Propio", nombre_periodo="Ciclo A")
        )
        proyecto = Proyecto.objects.get()
        self.assertEqual(
            (proyecto.marco_trabajo, proyecto.periodo_actual.nombre), ("Propio", "Ciclo A")
        )

    def test_fecha_fin_igual_a_inicio_es_valida(self):
        self.client.post(URL_NUEVO, datos_proyecto(fecha_fin="2026-12-12"))
        self.assertEqual(Proyecto.objects.count(), 1)


class MisProyectosTests(BaseCU01):
    """Paso 1 y R4: tarjetas con nombre, marco, periodo actual y métricas en meta."""

    def test_sin_proyectos_muestra_estado_vacio(self):
        respuesta = self.client.get(URL_MIS_PROYECTOS)
        self.assertContains(respuesta, "Todavía no tienes proyectos")
        self.assertContains(respuesta, "+ Nuevo proyecto")

    def test_tarjeta_muestra_datos_del_proyecto(self):
        self.crear_proyecto()
        respuesta = self.client.get(URL_MIS_PROYECTOS)
        self.assertContains(respuesta, "Dashboard SQA")
        self.assertContains(respuesta, "Kanban · Periodo actual: Entrega 1")
        self.assertContains(respuesta, "12/12/2026 – 24/12/2026")
        self.assertContains(respuesta, "Métricas en meta: 0/5")
        self.assertContains(respuesta, "Nuevo periodo")

    def test_periodo_actual_es_el_de_inicio_mas_reciente(self):
        proyecto = self.crear_proyecto(periodos=(("Entrega 2", 20, 24), ("Entrega 1", 1, 10)))
        self.assertEqual(proyecto.periodo_actual.nombre, "Entrega 2")
        self.assertContains(self.client.get(URL_MIS_PROYECTOS), "Periodo actual: Entrega 2")

    def test_solo_muestra_proyectos_propios(self):
        beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        self.crear_proyecto(usuario=beto, nombre="Proyecto de Beto")
        self.crear_proyecto(nombre="Proyecto de Ana")
        respuesta = self.client.get(URL_MIS_PROYECTOS)
        self.assertContains(respuesta, "Proyecto de Ana")
        self.assertNotContains(respuesta, "Proyecto de Beto")


class FA1CampoObligatorioTests(BaseCU01):
    def test_campos_obligatorios_vacios(self):
        campos = ("nombre", "marco_trabajo", "nombre_periodo", "fecha_inicio", "fecha_fin")
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(**dict.fromkeys(campos, "")))
        self.assertEqual(respuesta.status_code, 200)
        for campo in campos:
            self.assertEqual(self.errores(respuesta, campo), ["Este campo es obligatorio"], campo)
        self.assertFalse(Proyecto.objects.exists())

    def test_solo_espacios_cuenta_como_vacio(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(nombre="   "))
        self.assertEqual(self.errores(respuesta, "nombre"), ["Este campo es obligatorio"])

    def test_conserva_lo_capturado_y_muestra_aviso(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(marco_trabajo=""))
        self.assertContains(respuesta, "No se guardó. Revisa los campos marcados")
        self.assertContains(respuesta, 'value="Dashboard SQA"')
        self.assertContains(respuesta, 'value="2026-12-12"')

    def test_longitud_maxima(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(nombre="x" * 101))
        self.assertTrue(self.errores(respuesta, "nombre"))
        self.assertFalse(Proyecto.objects.exists())


class FA2FechasTests(BaseCU01):
    def test_fecha_fin_anterior_a_inicio(self):
        respuesta = self.client.post(
            URL_NUEVO, datos_proyecto(fecha_inicio="2026-12-24", fecha_fin="2026-12-12")
        )
        self.assertEqual(
            self.errores(respuesta, "fecha_fin"),
            ["La fecha de fin debe ser igual o posterior a la de inicio"],
        )
        self.assertFalse(Proyecto.objects.exists())

    def test_fecha_invalida(self):
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(fecha_inicio="31/02/2026"))
        self.assertEqual(self.errores(respuesta, "fecha_inicio"), ["Escribe una fecha válida"])


class FA3NuevoPeriodoTests(BaseCU01):
    def setUp(self):
        super().setUp()
        self.proyecto = self.crear_proyecto()
        self.url = reverse("proyectos:nuevo_periodo", args=[self.proyecto.pk])

    def test_formulario_muestra_proyecto_solo_lectura_y_periodos(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Proyecto (solo lectura)")
        self.assertContains(respuesta, "disabled")
        self.assertContains(respuesta, "Entrega 1")
        self.assertContains(respuesta, "No puede repetirse dentro del proyecto")

    def test_registra_periodo_y_pasa_a_ser_el_actual(self):
        respuesta = self.client.post(self.url, datos_periodo())
        nuevo = Periodo.objects.get(nombre="Entrega 2")
        self.assertRedirects(respuesta, reverse("medidas:captura", args=[nuevo.pk]))
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.periodo_actual, nuevo)
        self.assertEqual(self.proyecto.periodos.count(), 2)
        self.assertEqual(Proyecto.objects.count(), 1)
        self.assertEqual(MetaProyecto.objects.count(), 5)

    def test_no_modifica_datos_del_proyecto(self):
        self.client.post(self.url, datos_periodo(nombre="Otro nombre", marco_trabajo="Scrum"))
        self.proyecto.refresh_from_db()
        self.assertEqual(
            (self.proyecto.nombre, self.proyecto.marco_trabajo), ("Dashboard SQA", "Kanban")
        )


class FA4TraslapeTests(BaseCU01):
    def setUp(self):
        super().setUp()
        self.proyecto = self.crear_proyecto()
        self.url = reverse("proyectos:nuevo_periodo", args=[self.proyecto.pk])

    def test_periodo_que_comparte_un_dia_se_rechaza(self):
        respuesta = self.client.post(self.url, datos_periodo(fecha_inicio="2026-12-24"))
        self.assertEqual(
            self.errores(respuesta, "fecha_inicio"),
            ["Las fechas se traslapan con el periodo Entrega 1 (12/12/2026 – 24/12/2026)"],
        )
        self.assertEqual(
            self.errores(respuesta, "fecha_fin"), ["El periodo debe empezar después del 24/12/2026"]
        )
        self.assertEqual(self.proyecto.periodos.count(), 1)

    def test_periodo_contenido_dentro_de_otro_se_rechaza(self):
        respuesta = self.client.post(
            self.url, datos_periodo(fecha_inicio="2026-12-15", fecha_fin="2026-12-16")
        )
        self.assertTrue(self.errores(respuesta, "fecha_inicio"))

    def test_periodo_al_dia_siguiente_se_acepta(self):
        self.client.post(self.url, datos_periodo(fecha_inicio="2026-12-25"))
        self.assertEqual(self.proyecto.periodos.count(), 2)

    def test_otro_proyecto_puede_tener_las_mismas_fechas(self):
        """R3: periodos de proyectos distintos sí pueden coincidir."""
        self.client.post(URL_NUEVO, datos_proyecto(nombre="Proyecto 2"))
        self.assertEqual(Proyecto.objects.count(), 2)


class FA5NombreRepetidoTests(BaseCU01):
    def test_nombre_de_proyecto_repetido(self):
        self.crear_proyecto()
        respuesta = self.client.post(URL_NUEVO, datos_proyecto(nombre="dashboard sqa"))
        self.assertEqual(
            self.errores(respuesta, "nombre"), ["Ya tienes un proyecto llamado dashboard sqa"]
        )
        self.assertEqual(Proyecto.objects.count(), 1)

    def test_otro_usuario_puede_usar_el_mismo_nombre(self):
        beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        self.crear_proyecto(usuario=beto)
        self.client.post(URL_NUEVO, datos_proyecto())
        self.assertEqual(Proyecto.objects.filter(nombre="Dashboard SQA").count(), 2)

    def test_nombre_de_periodo_repetido_en_el_proyecto(self):
        proyecto = self.crear_proyecto()
        respuesta = self.client.post(
            reverse("proyectos:nuevo_periodo", args=[proyecto.pk]),
            datos_periodo(nombre_periodo="Entrega 1"),
        )
        self.assertEqual(
            self.errores(respuesta, "nombre_periodo"),
            ["Este proyecto ya tiene un periodo llamado Entrega 1"],
        )


class EnvioRepetidoTests(BaseCU01):
    """Checklist de implementación #37: repetir el envío no duplica registros."""

    def test_reenviar_nuevo_proyecto_no_duplica(self):
        self.client.post(URL_NUEVO, datos_proyecto())
        self.client.post(URL_NUEVO, datos_proyecto())
        self.assertEqual(Proyecto.objects.count(), 1)

    def test_reenviar_nuevo_proyecto_no_duplica_metas_ni_periodos(self):
        self.client.post(URL_NUEVO, datos_proyecto())
        self.client.post(URL_NUEVO, datos_proyecto())
        self.assertEqual((MetaProyecto.objects.count(), Periodo.objects.count()), (5, 1))

    def test_reenviar_nuevo_periodo_no_duplica(self):
        proyecto = self.crear_proyecto()
        url = reverse("proyectos:nuevo_periodo", args=[proyecto.pk])
        self.client.post(url, datos_periodo())
        self.client.post(url, datos_periodo())
        self.assertEqual(proyecto.periodos.count(), 2)


class FE1CancelarTests(BaseCU01):
    def test_formulario_tiene_cancelar_con_confirmacion(self):
        respuesta = self.client.get(URL_NUEVO)
        self.assertContains(respuesta, 'id="cancelar"')
        self.assertContains(respuesta, "¿Cancelar el registro?")
        self.assertContains(respuesta, "Seguir capturando")
        self.assertContains(respuesta, "Sí, cancelar")

    def test_cancelar_regresa_a_mis_proyectos_sin_guardar(self):
        respuesta = self.client.get(URL_MIS_PROYECTOS)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Proyecto.objects.exists())


class SeguridadTests(BaseCU01):
    """Requisito especial 1 (R21), R20 y R23."""

    def setUp(self):
        super().setUp()
        beto = Usuario.objects.create_user("beto", "beto@ejemplo.com", CLAVE)
        self.ajeno = self.crear_proyecto(usuario=beto, nombre="Proyecto de Beto")

    def test_no_puede_abrir_periodo_en_proyecto_ajeno(self):
        url = reverse("proyectos:nuevo_periodo", args=[self.ajeno.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, datos_periodo()).status_code, 404)
        self.assertEqual(self.ajeno.periodos.count(), 1)

    def test_no_puede_ver_captura_de_periodo_ajeno(self):
        url = reverse("medidas:captura", args=[self.ajeno.periodo_actual.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_sin_sesion_pide_iniciar_sesion(self):
        self.client.logout()
        for url in (URL_MIS_PROYECTOS, URL_NUEVO):
            respuesta = self.client.get(url)
            self.assertRedirects(respuesta, f"{reverse('cuentas:iniciar_sesion')}?next={url}")

    def test_texto_malicioso_se_guarda_como_texto(self):
        nombre = "x'); DROP TABLE proyectos_proyecto;--"
        descripcion = "<script>alert(1)</script>"
        self.client.post(URL_NUEVO, datos_proyecto(nombre=nombre, descripcion=descripcion))
        self.assertTrue(Proyecto.objects.filter(nombre=nombre, descripcion=descripcion).exists())
        respuesta = self.client.get(URL_MIS_PROYECTOS)
        self.assertNotContains(respuesta, "<script>alert(1)</script>")

    def test_formulario_lleva_csrf(self):
        self.assertContains(self.client.get(URL_NUEVO), "csrfmiddlewaretoken")
