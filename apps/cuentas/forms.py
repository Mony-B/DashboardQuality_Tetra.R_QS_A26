from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class RegistroForm(UserCreationForm):
    """Crear cuenta con usuario y correo únicos (R1)."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "email")

    def clean_email(self):
        correo = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return correo
