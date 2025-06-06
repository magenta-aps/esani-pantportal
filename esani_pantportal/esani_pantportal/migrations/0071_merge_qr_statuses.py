from django.db import migrations

REMOVED = ("backbone_modtaget", "esani_modtaget")
REPLACED_BY = "pantsystem_modtaget"


def merge_qrbag_status(apps, schema_editor):
    QRBag = apps.get_model("esani_pantportal", "QRBag")
    num_updated = QRBag.objects.filter(status__in=REMOVED).update(status=REPLACED_BY)
    print(f"Updated {num_updated} QRBag objects to status = pantsystem_modtaget")


def merge_historicalqrbag_status(apps, schema_editor):
    HistoricalQRBag = apps.get_model("esani_pantportal", "HistoricalQRBag")
    num_updated = (
        HistoricalQRBag.objects.filter(status__in=REMOVED).update(status=REPLACED_BY)
    )
    print(
        f"Updated {num_updated} HistoricalQRBag objects to status = pantsystem_modtaget"
    )


def remove_unused_qrstatus_objects(apps, schema_editor):
    QRStatus = apps.get_model("esani_pantportal", "QRStatus")
    num_deleted = QRStatus.objects.filter(code__in=REMOVED).delete()
    print(f"Deleted {num_deleted} QRStatus objects")


class Migration(migrations.Migration):
    dependencies = [
        ("esani_pantportal", "0070_update_city_fields_to_fk"),
    ]

    operations = [
        migrations.RunPython(merge_qrbag_status),
        migrations.RunPython(merge_historicalqrbag_status),
        migrations.RunPython(remove_unused_qrstatus_objects),
    ]
