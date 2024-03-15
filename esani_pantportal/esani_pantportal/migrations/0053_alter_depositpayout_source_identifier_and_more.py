# Generated by Django 4.2.11 on 2024-03-15 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0052_create_manual_erp_mapping_objects"),
    ]

    operations = [
        migrations.AlterField(
            model_name="depositpayout",
            name="source_identifier",
            field=models.CharField(
                max_length=255,
                verbose_name="Kilde-ID (filnavn, URL eller brugernavn+dato)",
            ),
        ),
        migrations.AlterField(
            model_name="depositpayout",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("csv", "Clearing-rapporter (CSV)"),
                    ("api", "QR-sække (API)"),
                    ("manual", "Manuelt oprettet af esani-admin"),
                ],
                max_length=6,
                verbose_name="Kilde-type",
            ),
        ),
        migrations.AlterField(
            model_name="depositpayoutitem",
            name="location_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="depositpayoutitem",
            name="rvm_serial",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="erpproductmapping",
            name="specifier",
            field=models.CharField(
                choices=[
                    ("rvm", "Pant eller håndteringsgodtgørelse, fra automat"),
                    ("bag", "Pant eller håndteringsgodtgørelse, fra QR-pose"),
                    (
                        "manual",
                        "Pant eller håndteringsgodtgørelse, fra manuelt oprettede pant-data",
                    ),
                    ("0", "Små sække"),
                    ("1", "Store sække"),
                    ("9", "QR-koder til test"),
                ],
                max_length=10,
                verbose_name="Specifik type af varelinje",
            ),
        ),
    ]