from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("proyectos", "0002_periodo_medidas"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="periodo",
            name="defecto_critico_abierto",
        ),
    ]
