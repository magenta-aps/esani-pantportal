# Ceated by Nick on 2024-02-08
from django.db import migrations
from django.core.management.color import no_style
from django.db import connection


# https://www.calazan.com/how-to-reset-the-primary-key-sequence-in-postgresql-with-django/
# https://stackoverflow.com/questions/43663588/executing-djangos-sqlsequencereset-code-from-within-python
def fix_pk(apps, schema_editor):
    qrbag = apps.get_model("esani_pantportal", "QRBag")

    sequence_sql = connection.ops.sequence_reset_sql(no_style(), [qrbag])
    with connection.cursor() as cursor:
        for sql in sequence_sql:
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0033_historicalqrbag_id_qrbag_id"),
    ]

    operations = [
        migrations.RunPython(fix_pk),
    ]
