import traffic.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0002_junctionrecord_sensor_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="ControllerCommand",
            fields=[
                (
                    "command_id",
                    models.CharField(max_length=100, primary_key=True, serialize=False),
                ),
                ("junction_id", models.CharField(max_length=50)),
                ("target_signals", models.JSONField(default=dict)),
                ("status", models.CharField(default="PENDING", max_length=20)),
                (
                    "created_at",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
                ("acknowledged_at", models.BigIntegerField(blank=True, null=True)),
            ],
        ),
    ]
