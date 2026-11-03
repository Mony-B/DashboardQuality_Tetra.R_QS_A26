from django.contrib import admin

from .models import Periodo, Proyecto


class PeriodoInline(admin.TabularInline):
    model = Periodo
    extra = 0
    fields = ("nombre", "fecha_inicio", "fecha_fin")


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marco_trabajo", "usuario")
    inlines = [PeriodoInline]
