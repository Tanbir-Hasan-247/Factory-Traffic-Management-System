import traffic.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("junction_id", models.CharField(max_length=50)),
                ("event_type", models.CharField(max_length=50)),
                ("details", models.JSONField(default=dict)),
                (
                    "timestamp",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
            ],
        ),
        migrations.CreateModel(
            name="JunctionRecord",
            fields=[
                (
                    "id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("mode", models.CharField(default="AUTOMATIC", max_length=20)),
                (
                    "current_phase",
                    models.CharField(default="NORTH_SOUTH", max_length=50),
                ),
                ("transition_state", models.CharField(default="STABLE", max_length=20)),
                (
                    "state_entered_at",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
                (
                    "manual_direction",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "emergency_direction",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("desired_signals", models.JSONField(default=dict)),
                ("actual_signals", models.JSONField(default=dict)),
                (
                    "controller_status",
                    models.CharField(default="ONLINE", max_length=20),
                ),
                (
                    "last_controller_ack",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProcessedEvent",
            fields=[
                (
                    "event_id",
                    models.CharField(max_length=100, primary_key=True, serialize=False),
                ),
                (
                    "timestamp",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                (
                    "vehicle_id",
                    models.CharField(max_length=100, primary_key=True, serialize=False),
                ),
                ("junction_id", models.CharField(max_length=50)),
                ("direction", models.CharField(max_length=20)),
                ("vehicle_type", models.CharField(max_length=50)),
                ("priority", models.IntegerField(default=1)),
                (
                    "arrival_time",
                    models.BigIntegerField(default=traffic.models.current_milli_time),
                ),
            ],
        ),
    ]
