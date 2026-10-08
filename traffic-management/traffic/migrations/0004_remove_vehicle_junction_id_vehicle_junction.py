import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0003_controllercommand"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vehicle",
            name="junction_id",
        ),
        migrations.AddField(
            model_name="vehicle",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                default="A",
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic.junctionrecord",
            ),
            preserve_default=False,
        ),
    ]
