"""Rutas raíz. Cada app registra las suyas con su propio namespace."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.cuentas.urls")),
    path("proyectos/", include("apps.proyectos.urls")),
    path("periodos/", include("apps.medidas.urls")),
    path("", include("apps.core.urls")),
]
