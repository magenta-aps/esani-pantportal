from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):
    dependencies = [
        ("esani_pantportal", "0070_update_city_fields_to_fk"),
    ]

    operations = [
        TrigramExtension(),
    ]
