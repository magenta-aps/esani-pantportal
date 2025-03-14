# Generated by Django 4.2.11 on 2025-03-14 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0065_alter_depositpayoutitem_rvm_serial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="fasttrack_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Vælges, hvis denne bruger har adgang til fasttrack i Utertitsisa-app'en",
                verbose_name="Fasttrack",
            ),
        ),
    ]
