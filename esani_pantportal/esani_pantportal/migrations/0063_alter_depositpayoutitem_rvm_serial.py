# Generated by Django 4.2.11 on 2024-10-24 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0062_alter_historicalqrbag_status_alter_qrbag_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="depositpayoutitem",
            name="rvm_serial",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
