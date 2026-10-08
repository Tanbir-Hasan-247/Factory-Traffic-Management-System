import traffic.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0005_remove_controllercommand_junction_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="junctionrecord",
            name="pending_command_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="actual_signals",
            field=models.JSONField(default=traffic.models.default_actual_signals),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="current_phase",
            field=models.CharField(default="ALL_RED", max_length=50),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="desired_signals",
            field=models.JSONField(default=traffic.models.default_desired_signals),
        ),
    ]
