import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Proyecto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100)),
                ("marco_trabajo", models.CharField(max_length=50, verbose_name="marco de trabajo")),
                ("descripcion", models.CharField(blank=True, max_length=500, verbose_name="descripción")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proyectos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Periodo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=50)),
                ("fecha_inicio", models.DateField(verbose_name="fecha de inicio")),
                ("fecha_fin", models.DateField(verbose_name="fecha de fin")),
                ("funciones_requeridas", models.PositiveIntegerField(blank=True, null=True)),
                ("funciones_entregadas", models.PositiveIntegerField(blank=True, null=True)),
                ("casos_ejecutados", models.PositiveIntegerField(blank=True, null=True)),
                ("casos_aprobados", models.PositiveIntegerField(blank=True, null=True)),
                ("requisitos_verificables", models.PositiveIntegerField(blank=True, null=True)),
                ("requisitos_con_prueba", models.PositiveIntegerField(blank=True, null=True)),
                ("defectos_codigo", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "kloc",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=8,
                        null=True,
                        verbose_name="tamaño del código (KLOC)",
                    ),
                ),
                (
                    "defecto_critico_abierto",
                    models.BooleanField(default=False, verbose_name="existe un defecto crítico abierto"),
                ),
                (
                    "proyecto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="periodos",
                        to="proyectos.proyecto",
                    ),
                ),
            ],
            options={
                "ordering": ["-fecha_inicio"],
            },
        ),
        migrations.AddConstraint(
            model_name="proyecto",
            constraint=models.UniqueConstraint(fields=("usuario", "nombre"), name="proyecto_nombre_unico"),
        ),
        migrations.AddConstraint(
            model_name="periodo",
            constraint=models.UniqueConstraint(fields=("proyecto", "nombre"), name="periodo_nombre_unico"),
        ),
        migrations.AddConstraint(
            model_name="periodo",
            constraint=models.CheckConstraint(
                condition=models.Q(("kloc__isnull", True), ("kloc__gt", 0), _connector="OR"),
                name="periodo_kloc_mayor_que_cero",
            ),
        ),
    ]
