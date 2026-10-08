import django.db.models.deletion
import traffic.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0004_remove_vehicle_junction_id_vehicle_junction"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="controllercommand",
            name="junction_id",
        ),
        migrations.RemoveField(
            model_name="processedevent",
            name="timestamp",
        ),
        migrations.AddField(
            model_name="controllercommand",
            name="junction",
            field=models.ForeignKey(
                db_column="junction_id",
                default="A",
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic.junctionrecord",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="processedevent",
            name="event_type",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="processedevent",
            name="junction",
            field=models.ForeignKey(
                blank=True,
                db_column="junction_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic.junctionrecord",
            ),
        ),
        migrations.AddField(
            model_name="processedevent",
            name="received_at",
            field=models.BigIntegerField(default=traffic.models.current_milli_time),
        ),
        migrations.AddField(
            model_name="processedevent",
            name="sensor_timestamp",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="processedevent",
            name="sequence_no",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
