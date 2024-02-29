# Generated by Django 4.2.2 on 2024-02-29 14:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0048_depositpayoutitem_file_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="show_approval_date",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_approved",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_branch",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_capacity",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_account_number",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_address",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_branch_type",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_city",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_company",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_company_type",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_country",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_customer_id",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_cvr",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_invoice_company_branch",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_invoice_mail",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_location_id",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_municipality",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_phone",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_postal_code",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_qr_compensation",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_company_registration_number",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_creation_date",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_danish",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_diameter",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_email",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_file_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_height",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_is_admin",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_material",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_newsletter",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_phone",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_shape",
        ),
        migrations.RemoveField(
            model_name="user",
            name="show_weight",
        ),
        migrations.CreateModel(
            name="UserListViewPreferences",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "show_branch",
                    models.BooleanField(default=True, verbose_name="Butik"),
                ),
                (
                    "show_company",
                    models.BooleanField(default=True, verbose_name="Virksomhed"),
                ),
                (
                    "show_is_admin",
                    models.BooleanField(
                        default=True, verbose_name="Har admin-rettigheder"
                    ),
                ),
                (
                    "show_approved",
                    models.BooleanField(default=True, verbose_name="Godkendt"),
                ),
                (
                    "show_phone",
                    models.BooleanField(default=False, verbose_name="Telefonnummer"),
                ),
                (
                    "show_newsletter",
                    models.BooleanField(
                        default=False, verbose_name="Modtager Nyhedsbreve"
                    ),
                ),
                ("show_email", models.BooleanField(default=False, verbose_name="Mail")),
                (
                    "user",
                    models.OneToOneField(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user_list_view_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProductListViewPreferences",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "show_material",
                    models.BooleanField(default=True, verbose_name="Materiale"),
                ),
                ("show_shape", models.BooleanField(default=True, verbose_name="Form")),
                (
                    "show_danish",
                    models.BooleanField(default=True, verbose_name="Dansk pant"),
                ),
                (
                    "show_height",
                    models.BooleanField(default=False, verbose_name="Højde"),
                ),
                (
                    "show_diameter",
                    models.BooleanField(default=False, verbose_name="Diameter"),
                ),
                (
                    "show_weight",
                    models.BooleanField(default=False, verbose_name="Vægt"),
                ),
                (
                    "show_capacity",
                    models.BooleanField(default=False, verbose_name="Volumen"),
                ),
                (
                    "show_approval_date",
                    models.BooleanField(default=False, verbose_name="Godkendt dato"),
                ),
                (
                    "show_creation_date",
                    models.BooleanField(default=False, verbose_name="Oprettelsesdato"),
                ),
                (
                    "show_file_name",
                    models.BooleanField(default=False, verbose_name="Filnavn"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="product_list_view_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CompanyListViewPreferences",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "show_address",
                    models.BooleanField(default=True, verbose_name="Adresse"),
                ),
                (
                    "show_postal_code",
                    models.BooleanField(default=False, verbose_name="Postnr."),
                ),
                (
                    "show_municipality",
                    models.BooleanField(default=True, verbose_name="Kommune"),
                ),
                ("show_city", models.BooleanField(default=True, verbose_name="By")),
                (
                    "show_country",
                    models.BooleanField(default=False, verbose_name="Land"),
                ),
                (
                    "show_phone",
                    models.BooleanField(default=False, verbose_name="Telefonnummer"),
                ),
                (
                    "show_registration_number",
                    models.BooleanField(
                        default=False, verbose_name="Registreringsnummer"
                    ),
                ),
                (
                    "show_account_number",
                    models.BooleanField(default=False, verbose_name="Kontonummer"),
                ),
                (
                    "show_invoice_mail",
                    models.BooleanField(default=False, verbose_name="Fakturamail"),
                ),
                (
                    "show_company_type",
                    models.BooleanField(default=False, verbose_name="Virksomhedstype"),
                ),
                (
                    "show_branch_type",
                    models.BooleanField(default=False, verbose_name="Butikstype"),
                ),
                (
                    "show_invoice_company_branch",
                    models.BooleanField(
                        default=False, verbose_name="Faktura til butik"
                    ),
                ),
                (
                    "show_location_id",
                    models.BooleanField(default=False, verbose_name="Lokation ID"),
                ),
                (
                    "show_customer_id",
                    models.BooleanField(default=False, verbose_name="Kunde ID"),
                ),
                (
                    "show_qr_compensation",
                    models.BooleanField(
                        default=False,
                        verbose_name="Håndterings-godtgørelse for QR-poser",
                    ),
                ),
                (
                    "show_company",
                    models.BooleanField(default=False, verbose_name="Virksomhed"),
                ),
                ("show_cvr", models.BooleanField(default=False, verbose_name="CVR")),
                (
                    "user",
                    models.OneToOneField(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="company_list_view_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
