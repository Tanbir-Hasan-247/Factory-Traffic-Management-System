from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0006_junctionrecord_pending_command_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="junctionrecord",
            name="controller_status",
            field=models.CharField(default="UNKNOWN", max_length=20),
        ),
    ]
