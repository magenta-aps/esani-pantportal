# Generated by Django 4.2.2 on 2024-02-06 12:35
# Edited by Nick on 2024-02-06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0031_rename_companybranch_to_company_branch"),
    ]

    operations = [
        migrations.RenameField(
            model_name="reversevendingmachine",
            old_name="branch",
            new_name="company_branch",
        ),
    ]