# Ceated by Nick on 2024-02-15
from django.db import migrations

from esani_pantportal.models import MUNICIPALITY_CHOICES


MUNICIPALITY_AVANNAATA = MUNICIPALITY_CHOICES[0][0]
MUNICIPALITY_KUJALLEQ = MUNICIPALITY_CHOICES[1][0]
MUNICIPALITY_QEQERTALIK = MUNICIPALITY_CHOICES[2][0]
MUNICIPALITY_SERMERSOOQ = MUNICIPALITY_CHOICES[3][0]
MUNICIPALITY_QEQQATA = MUNICIPALITY_CHOICES[4][0]
MUNICIPALITY_OTHER = MUNICIPALITY_CHOICES[len(MUNICIPALITY_CHOICES) - 1][0]

municipalities_cleanup_map = {
    MUNICIPALITY_AVANNAATA: [
        "avannaata",
        "Avannaata",
        "Avaanaata",
        "Avannaata kommune",
        "avannaata kommunia",
    ],
    MUNICIPALITY_KUJALLEQ: ["Kujalleq", "Komunia Kujalleq"],
    MUNICIPALITY_QEQERTALIK: ["Qeqertalik", "Qeqerlik"],
    MUNICIPALITY_SERMERSOOQ: [
        "Nuuk",
        "sermersooq",
        "Sermersooq",
        "Seermersoq",
        "Sermasooq",
        "Seermasooq",
        "Sermersooq Kommunia",
    ],
    MUNICIPALITY_QEQQATA: ["Qeqqata", "qeqqata"],
    MUNICIPALITY_OTHER: [
        None,
        "",
        "Skive",
        "Ishøj",
        "Aalborg",
        "Vejle",
        "Albertslund",
    ],
}


def cleanup_company_municipality(apps, schema_editor):
    company_model = apps.get_model("esani_pantportal", "Company")
    for db_model in company_model.objects.all():
        for replace_value, invalid_values in municipalities_cleanup_map.items():
            if (
                db_model.municipality not in invalid_values
                or db_model.municipality == replace_value
            ):
                continue

            print(f"Replacing '{db_model.municipality}' with '{replace_value}'")
            db_model.municipality = replace_value
            db_model.save()

    branch_model = apps.get_model("esani_pantportal", "CompanyBranch")
    for db_model in branch_model.objects.all():
        for replace_value, invalid_values in municipalities_cleanup_map.items():
            if (
                db_model.municipality not in invalid_values
                or db_model.municipality == replace_value
            ):
                continue

            print(f"Replacing '{db_model.municipality}' with '{replace_value}'")
            db_model.municipality = replace_value
            db_model.save()

    kiosk_model = apps.get_model("esani_pantportal", "Kiosk")
    for db_model in kiosk_model.objects.all():
        for replace_value, invalid_values in municipalities_cleanup_map.items():
            if (
                db_model.municipality not in invalid_values
                or db_model.municipality == replace_value
            ):
                continue

            print(f"Replacing '{db_model.municipality}' with '{replace_value}'")
            db_model.municipality = replace_value
            db_model.save()


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0042_cleanup_phone_numbers"),
    ]

    operations = [
        migrations.RunPython(cleanup_company_municipality),
    ]
