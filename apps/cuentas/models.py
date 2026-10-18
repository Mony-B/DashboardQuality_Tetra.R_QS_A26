from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuario del sistema: integrante de un equipo que monitorea su proyecto.

    Se define desde el inicio (aunque por ahora solo cambia el correo) porque
    cambiar el modelo de usuario después de la primera migración es muy costoso.
    """

    email = models.EmailField("correo electrónico", unique=True)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.username
