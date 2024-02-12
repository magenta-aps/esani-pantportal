# Generated by Django 4.2.2 on 2024-02-12 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0036_alter_qrbag_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="invoice_company_branch",
            field=models.BooleanField(
                default=True,
                verbose_name="Send faktura/kreditnota/mv. til den enkelte butik",
            ),
        ),
    ]
