from django.contrib import admin

from .models import Actividad


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ("tecnica", "artefacto", "responsable", "fecha", "estado", "periodo")
    list_filter = ("estado", "tecnica")
