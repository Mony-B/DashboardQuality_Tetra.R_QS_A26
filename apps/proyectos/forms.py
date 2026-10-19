from django import forms
from django.db import transaction

from .models import Periodo, Proyecto

OBLIGATORIO = {"required": "Este campo es obligatorio"}


def _fecha(valor):
    return valor.strftime("%d/%m/%Y")


def _selector_fecha():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class ProyectoPeriodoForm(forms.Form):
    """Formulario "Nuevo proyecto / nuevo periodo" del CU 01.

    Sin ``proyecto`` registra un proyecto y su primer periodo (flujo normal).
    Con ``proyecto`` solo abre un periodo nuevo: los datos del proyecto se muestran
    de solo lectura y además se valida traslape y nombre de periodo (FA-3 a FA-5).
    """

    nombre = forms.CharField(
        label="Nombre del proyecto",
        max_length=100,
        error_messages=OBLIGATORIO,
        help_text="Máximo 100 caracteres",
        widget=forms.TextInput(attrs={"placeholder": "Ej. Dashboard SQA"}),
    )
    marco_trabajo = forms.CharField(
        label="Marco de trabajo",
        max_length=50,
        error_messages=OBLIGATORIO,
        help_text="Texto libre · máximo 50 caracteres",
        widget=forms.TextInput(attrs={"placeholder": "Ej. Kanban, cascada, propio"}),
    )
    descripcion = forms.CharField(
        label="Descripción (opcional)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Máximo 500 caracteres"}),
    )
    nombre_periodo = forms.CharField(
        label="Nombre del periodo",
        max_length=50,
        error_messages=OBLIGATORIO,
        help_text="Texto libre · máximo 50 caracteres",
        widget=forms.TextInput(attrs={"placeholder": "Ej. Entrega 1, Iteración 1"}),
    )
    fecha_inicio = forms.DateField(
        label="Fecha de inicio",
        error_messages={**OBLIGATORIO, "invalid": "Escribe una fecha válida"},
        widget=_selector_fecha(),
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        error_messages={**OBLIGATORIO, "invalid": "Escribe una fecha válida"},
        widget=_selector_fecha(),
    )

    campos_proyecto = ("nombre", "marco_trabajo", "descripcion")
    campos_periodo = ("nombre_periodo", "fecha_inicio", "fecha_fin")

    def __init__(self, *args, usuario, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.proyecto = proyecto
        if proyecto is not None:
            # FA-3: los datos del proyecto son de solo lectura; lo que llegue en el POST se ignora.
            for nombre in self.campos_proyecto:
                campo = self.fields[nombre]
                campo.disabled = True
                campo.required = False
                campo.help_text = ""
                campo.widget.attrs.pop("placeholder", None)
                self.initial[nombre] = getattr(proyecto, nombre)
            self.fields["nombre_periodo"].help_text = "No puede repetirse dentro del proyecto"
            del self.fields["descripcion"]

    @property
    def es_periodo_nuevo(self):
        return self.proyecto is not None

    def secciones(self):
        """Campos agrupados como en el wireframe: PROYECTO y PRIMER PERIODO / PERIODO NUEVO."""
        return (
            [self[n] for n in self.campos_proyecto if n in self.fields],
            [self[n] for n in self.campos_periodo],
        )

    def clean(self):
        datos = super().clean()
        nombre = datos.get("nombre")
        nombre_periodo = datos.get("nombre_periodo")
        inicio = datos.get("fecha_inicio")
        fin = datos.get("fecha_fin")

        # FA-5: nombre de proyecto repetido entre los proyectos del usuario.
        if not self.es_periodo_nuevo and nombre:
            if Proyecto.objects.filter(usuario=self.usuario, nombre__iexact=nombre).exists():
                self.add_error("nombre", f"Ya tienes un proyecto llamado {nombre}")

        # FA-2: fecha de fin anterior a la de inicio.
        if inicio and fin and fin < inicio:
            self.add_error("fecha_fin", "La fecha de fin debe ser igual o posterior a la de inicio")
            return datos

        if self.es_periodo_nuevo:
            # FA-5: nombre de periodo repetido dentro del proyecto.
            if (
                nombre_periodo
                and self.proyecto.periodos.filter(nombre__iexact=nombre_periodo).exists()
            ):
                self.add_error(
                    "nombre_periodo", f"Este proyecto ya tiene un periodo llamado {nombre_periodo}"
                )
            # FA-4: periodo traslapado dentro del mismo proyecto.
            if inicio and fin:
                nuevo = Periodo(proyecto=self.proyecto, fecha_inicio=inicio, fecha_fin=fin)
                traslapados = list(nuevo.traslapes())
                if traslapados:
                    p = traslapados[0]
                    self.add_error(
                        "fecha_inicio",
                        f"Las fechas se traslapan con el periodo {p.nombre} "
                        f"({_fecha(p.fecha_inicio)} – {_fecha(p.fecha_fin)})",
                    )
                    ultimo_fin = max(t.fecha_fin for t in traslapados)
                    self.add_error(
                        "fecha_fin", f"El periodo debe empezar después del {_fecha(ultimo_fin)}"
                    )
        return datos

    @transaction.atomic
    def save(self):
        """Registra el proyecto (con sus 5 metas sugeridas) y el periodo; devuelve el periodo."""
        datos = self.cleaned_data
        proyecto = self.proyecto
        if proyecto is None:
            proyecto = Proyecto.objects.create(
                usuario=self.usuario,
                nombre=datos["nombre"],
                marco_trabajo=datos["marco_trabajo"],
                descripcion=datos["descripcion"],
            )
            proyecto.crear_metas_sugeridas()
        return Periodo.objects.create(
            proyecto=proyecto,
            nombre=datos["nombre_periodo"],
            fecha_inicio=datos["fecha_inicio"],
            fecha_fin=datos["fecha_fin"],
        )
