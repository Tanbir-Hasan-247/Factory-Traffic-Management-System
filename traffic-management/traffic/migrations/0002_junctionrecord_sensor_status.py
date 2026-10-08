from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="junctionrecord",
            name="sensor_status",
            field=models.JSONField(default=dict),
        ),
    ]
