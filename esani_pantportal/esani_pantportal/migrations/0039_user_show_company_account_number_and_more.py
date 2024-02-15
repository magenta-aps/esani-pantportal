# Generated by Django 4.2.2 on 2024-02-14 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0038_erpproductmapping"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="show_company_account_number",
            field=models.BooleanField(default=False, verbose_name="Kontonummer"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_address",
            field=models.BooleanField(default=True, verbose_name="Adresse"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_branch_type",
            field=models.BooleanField(default=False, verbose_name="Butikstype"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_city",
            field=models.BooleanField(default=True, verbose_name="By"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_company",
            field=models.BooleanField(default=False, verbose_name="Virksomhed"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_company_type",
            field=models.BooleanField(default=False, verbose_name="Virksomhedstype"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_country",
            field=models.BooleanField(default=False, verbose_name="Land"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_customer_id",
            field=models.BooleanField(default=False, verbose_name="Kunde ID"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_cvr",
            field=models.BooleanField(default=False, verbose_name="CVR"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_invoice_company_branch",
            field=models.BooleanField(default=False, verbose_name="Faktura til butik"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_invoice_mail",
            field=models.BooleanField(default=False, verbose_name="Fakturamail"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_location_id",
            field=models.BooleanField(default=False, verbose_name="Lokation ID"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_municipality",
            field=models.BooleanField(default=True, verbose_name="Kommune"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_phone",
            field=models.BooleanField(default=False, verbose_name="Telefonnummer"),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_postal_code",
            field=models.BooleanField(default=False, verbose_name="Postnr."),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_qr_compensation",
            field=models.BooleanField(
                default=False, verbose_name="Håndterings-godtgørelse for QR-poser"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company_registration_number",
            field=models.BooleanField(
                default=False, verbose_name="Registreringsnummer"
            ),
        ),
    ]