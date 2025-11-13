# Generated migration to delete Transferencia model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_alter_archivocarga_options_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Transferencia",
        ),
    ]
