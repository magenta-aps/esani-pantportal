# Generated by Django 4.2.11 on 2024-04-08 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0054_depositpayoutitem_compensation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companybranch",
            name="qr_compensation",
            field=models.FloatField(
                default=0,
                help_text="Håndteringsgodtgørelse for QR-poser, angivet i øre (100=1DKK, 25=0.25DKK)",
                verbose_name="Håndteringsgodtgørelse for QR-poser",
            ),
        ),
        migrations.AlterField(
            model_name="companylistviewpreferences",
            name="show_qr_compensation",
            field=models.BooleanField(
                default=False, verbose_name="Håndteringsgodtgørelse for QR-poser"
            ),
        ),
        migrations.AlterField(
            model_name="depositpayoutitem",
            name="compensation",
            field=models.PositiveSmallIntegerField(
                blank=True,
                default=None,
                help_text="Håndteringsgodtgørelse, angivet i øre (100=1DKK, 25=0.25DKK)",
                null=True,
                verbose_name="Håndteringsgodtgørelse",
            ),
        ),
        migrations.AlterField(
            model_name="kiosk",
            name="qr_compensation",
            field=models.FloatField(
                default=0,
                help_text="Håndteringsgodtgørelse for QR-poser, angivet i øre (100=1DKK, 25=0.25DKK)",
                verbose_name="Håndteringsgodtgørelse for QR-poser",
            ),
        ),
        migrations.AlterField(
            model_name="reversevendingmachine",
            name="compensation",
            field=models.FloatField(
                default=0,
                help_text="Håndteringsgodtgørelse, angivet i øre (100=1DKK, 25=0.25DKK)",
                verbose_name="Håndteringsgodtgørelse",
            ),
        ),
    ]