# Generated by Django 4.2.2 on 2024-02-09 10:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0035_user_show_approved_user_show_branch_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="qrbag",
            options={"ordering": ["-updated"]},
        ),
    ]
