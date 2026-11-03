from django import forms
from django.core.validators import URLValidator

from .models import Actividad

MSG_ENLACE = "Escribe un enlace válido que empiece con http:// o https://."
_validar_url = URLValidator(schemes=["http", "https"])


class ActividadForm(forms.ModelForm):
    """Datos de una actividad nueva (paso 6 y FA-1): los cuatro son obligatorios."""

    tecnica = forms.ChoiceField(
        label="Técnica",
        choices=[("", "Elige una técnica"), *Actividad.Tecnica.choices],
        error_messages={
            "required": "Elige una técnica.",
            "invalid_choice": "Elige una técnica.",
        },
    )
    artefacto = forms.CharField(
        label="Artefacto o caso de uso",
        max_length=120,
        error_messages={
            "required": "Escribe el artefacto o caso de uso.",
            "max_length": "Máximo 120 caracteres.",
        },
        widget=forms.TextInput(attrs={"placeholder": "Ej. CU 01", "maxlength": 120}),
    )
    responsable = forms.CharField(
        label="Responsable",
        max_length=80,
        error_messages={
            "required": "Escribe el responsable.",
            "max_length": "Máximo 80 caracteres.",
        },
        widget=forms.TextInput(attrs={"placeholder": "Ej. Integrante 1", "maxlength": 80}),
    )
    fecha = forms.DateField(
        label="Fecha",
        error_messages={"required": "Elige la fecha.", "invalid": "Elige una fecha válida."},
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = Actividad
        fields = ("tecnica", "artefacto", "responsable", "fecha")


class EstadoForm(forms.Form):
    estado = forms.ChoiceField(choices=Actividad.Estado.choices)


class EnlaceForm(forms.Form):
    """Enlace a la evidencia: vacío (lo quita) o una URL http:// o https:// (R9)."""

    enlace = forms.CharField(
        required=False,
        max_length=500,
        error_messages={"max_length": "El enlace no puede pasar de 500 caracteres."},
    )

    def clean_enlace(self):
        enlace = self.cleaned_data["enlace"]
        if enlace:
            try:
                _validar_url(enlace)
            except forms.ValidationError:
                raise forms.ValidationError(MSG_ENLACE) from None
        return enlace
