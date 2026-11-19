from django.db import migrations


class Migration(migrations.Migration):
    """Las metas por proyecto ya no existen: umbrales y pesos son fijos (CU 04)."""

    dependencies = [
        ("proyectos", "0003_quitar_defecto_critico"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MetaProyecto",
        ),
    ]
