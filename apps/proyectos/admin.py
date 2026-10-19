from django.contrib import admin

from .models import MetaProyecto, Periodo, Proyecto


class PeriodoInline(admin.TabularInline):
    model = Periodo
    extra = 0


class MetaInline(admin.TabularInline):
    model = MetaProyecto
    extra = 0


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marco_trabajo", "usuario", "creado")
    list_filter = ("usuario",)
    inlines = [PeriodoInline, MetaInline]
