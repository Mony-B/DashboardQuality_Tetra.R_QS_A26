from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proyectos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="periodo",
            name="funciones_requeridas",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="funciones_entregadas",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="casos_ejecutados",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="casos_aprobados",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="requisitos_verificables",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="requisitos_con_prueba",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="defectos_codigo",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="kloc",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=8,
                null=True,
                verbose_name="tamaño del código (KLOC)",
            ),
        ),
        migrations.AddField(
            model_name="periodo",
            name="defecto_critico_abierto",
            field=models.BooleanField(default=False, verbose_name="existe un defecto crítico abierto"),
        ),
        migrations.AddConstraint(
            model_name="periodo",
            constraint=models.CheckConstraint(
                condition=models.Q(("kloc__isnull", True), ("kloc__gt", 0), _connector="OR"),
                name="periodo_kloc_mayor_que_cero",
            ),
        ),
    ]
