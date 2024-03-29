# Generated by Django 4.2.2 on 2024-01-05 12:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('esani_pantportal', '0016_alter_companybranch_options_alter_kiosk_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='branchuser',
            options={'verbose_name': 'Butiks bruger', 'verbose_name_plural': 'Butiks brugere'},
        ),
        migrations.AlterModelOptions(
            name='companybranch',
            options={'verbose_name': 'Butik', 'verbose_name_plural': 'Butikker'},
        ),
        migrations.AlterModelOptions(
            name='companyuser',
            options={'verbose_name': 'Virksomheds bruger', 'verbose_name_plural': 'Virksomheds brugere'},
        ),
        migrations.AlterModelOptions(
            name='esaniuser',
            options={'verbose_name': 'Esani bruger', 'verbose_name_plural': 'Esani brugere'},
        ),
        migrations.AlterModelOptions(
            name='kiosk',
            options={'verbose_name': 'Kiosk', 'verbose_name_plural': 'Kiosker'},
        ),
        migrations.AlterModelOptions(
            name='kioskuser',
            options={'verbose_name': 'Kiosk bruger', 'verbose_name_plural': 'Kiosk brugere'},
        ),
        migrations.AlterModelOptions(
            name='refundmethod',
            options={'ordering': ['serial_number'], 'verbose_name': 'Pant metode', 'verbose_name_plural': 'Pant metoder'},
        ),
        migrations.AlterModelOptions(
            name='sentemail',
            options={'verbose_name': 'Sendte emails'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['username'], 'verbose_name': 'Bruger', 'verbose_name_plural': 'Brugere'},
        ),
    ]
