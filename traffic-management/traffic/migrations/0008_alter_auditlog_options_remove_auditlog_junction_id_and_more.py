import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0007_alter_junctionrecord_controller_status"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="auditlog",
            options={"ordering": ["-timestamp"]},
        ),
        migrations.RemoveField(
            model_name="auditlog",
            name="junction_id",
        ),
        migrations.AddField(
            model_name="auditlog",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                default="A",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audit_logs",
                to="traffic.junctionrecord",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="junctionrecord",
            name="transition_target_phase",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="controllercommand",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="controller_commands",
                to="traffic.junctionrecord",
            ),
        ),
        migrations.AlterField(
            model_name="controllercommand",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("ACKED", "Acknowledged"),
                    ("FAILED", "Failed"),
                    ("TIMEOUT", "Timeout"),
                    ("STALE", "Stale"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="controller_status",
            field=models.CharField(
                choices=[
                    ("UNKNOWN", "Unknown"),
                    ("ONLINE", "Online"),
                    ("OFFLINE", "Offline"),
                ],
                default="UNKNOWN",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="current_phase",
            field=models.CharField(
                choices=[
                    ("NORTH_SOUTH", "North South"),
                    ("EAST_WEST", "East West"),
                    ("ALL_RED", "All Red"),
                ],
                default="ALL_RED",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="last_controller_ack",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="junctionrecord",
            name="mode",
            field=models.CharField(
                choices=[
                    ("AUTOMATIC", "Automatic"),
                    ("MANUAL", "Manual"),
                    ("EMERGENCY", "Emergency"),
                    ("DEGRADED", "Degraded"),
                ],
                default="AUTOMATIC",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="processedevent",
            name="event_type",
            field=models.CharField(default="A", max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="processedevent",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                default="A",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="processed_events",
                to="traffic.junctionrecord",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="vehicles",
                to="traffic.junctionrecord",
            ),
        ),
    ]
