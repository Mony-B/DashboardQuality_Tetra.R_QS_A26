import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("proyectos", "0002_periodo_medidas"),
    ]

    operations = [
        migrations.CreateModel(
            name="Actividad",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "tecnica",
                    models.CharField(
                        choices=[
                            ("revision_personal", "Revisión personal"),
                            ("revision_pares", "Revisión entre pares"),
                            ("analisis_estatico", "Análisis estático"),
                            ("prueba_unitaria", "Prueba unitaria"),
                            ("prueba_integracion", "Prueba de integración"),
                            ("prueba_seguridad", "Prueba de seguridad"),
                        ],
                        max_length=30,
                        verbose_name="técnica",
                    ),
                ),
                (
                    "artefacto",
                    models.CharField(max_length=120, verbose_name="artefacto o caso de uso"),
                ),
                ("responsable", models.CharField(max_length=80)),
                ("fecha", models.DateField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("planeada", "Planeada"),
                            ("en_curso", "En curso"),
                            ("completada", "Completada"),
                        ],
                        default="planeada",
                        max_length=20,
                    ),
                ),
                (
                    "enlace_evidencia",
                    models.CharField(
                        blank=True, max_length=500, verbose_name="enlace a la evidencia"
                    ),
                ),
                ("creada", models.DateTimeField(auto_now_add=True)),
                (
                    "periodo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actividades",
                        to="proyectos.periodo",
                    ),
                ),
            ],
            options={
                "verbose_name": "actividad SQA",
                "verbose_name_plural": "actividades SQA",
                "ordering": ["id"],
            },
        ),
    ]
