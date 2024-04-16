# Generated by Django 4.2.11 on 2024-04-16 08:13

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0060_merge_20240411_1111"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalproduct",
            name="state",
            field=django_fsm.FSMField(
                choices=[
                    ("afventer", "Afventer godkendelse"),
                    ("godkendt", "Godkendt"),
                    ("afvist", "Afvist"),
                    ("slettet", "Slettet"),
                ],
                db_index=True,
                default="afventer",
                max_length=50,
                protected=True,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="state",
            field=django_fsm.FSMField(
                choices=[
                    ("afventer", "Afventer godkendelse"),
                    ("godkendt", "Godkendt"),
                    ("afvist", "Afvist"),
                    ("slettet", "Slettet"),
                ],
                db_index=True,
                default="afventer",
                max_length=50,
                protected=True,
                verbose_name="Status",
            ),
        ),
    ]