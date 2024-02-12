# Generated by Django 4.2.2 on 2024-02-08 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0034_fix_qrbag_pk"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="show_approved",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="show_branch",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="show_company",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="show_email",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="show_is_admin",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="show_newsletter",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="show_phone",
            field=models.BooleanField(default=False),
        ),
    ]