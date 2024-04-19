from django.db import migrations, models
import django.db.models.deletion


def populate_history_relation(apps, schema_editor) -> None:
    HistoricalProduct = apps.get_model("esani_pantportal", "HistoricalProduct")
    HistoricalProduct.objects.filter(history_relation=0).update(history_relation=models.F("id"))


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0056_remove_historicalproduct_approval_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalproduct",
            name="history_relation",
            field=models.ForeignKey(
                db_constraint=False,
                default=0,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="history_entries",
                to="esani_pantportal.product",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_history_relation),
    ]
