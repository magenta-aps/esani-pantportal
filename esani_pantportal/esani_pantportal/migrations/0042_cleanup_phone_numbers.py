# Ceated by Nick on 2024-02-15
from django.db import migrations

from .utils.utils import clean_phone_no


def format_phone_numbers(apps, schema_editor):

    model_names = [
        "EsaniUser",
        "BranchUser",
        "CompanyUser",
        "KioskUser",
        "Company",
        "CompanyBranch",
        "Kiosk",
    ]

    for model_name in model_names:
        model = apps.get_model("esani_pantportal", model_name)

        for obj in model.objects.all():
            phone = obj.phone
            obj.phone = clean_phone_no(phone)
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0041_backfill_short_qr_codes"),
    ]

    operations = [
        migrations.RunPython(format_phone_numbers),
    ]
