# Generated by Django 4.2.2 on 2023-12-11 12:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('esani_pantportal', '0002_depositpayout_depositpayoutitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productline',
            name='packaging_registration',
        ),
        migrations.RemoveField(
            model_name='productline',
            name='product',
        ),
        migrations.AlterField(
            model_name='branchuser',
            name='branch',
            field=models.ForeignKey(help_text='Butik hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='users', to='esani_pantportal.companybranch', verbose_name='Butik'),
        ),
        migrations.AlterField(
            model_name='companybranch',
            name='company',
            field=models.ForeignKey(help_text='Virksomhed som denne butik tilhører', on_delete=django.db.models.deletion.PROTECT, related_name='branches', to='esani_pantportal.company', verbose_name='Virksomhed'),
        ),
        migrations.AlterField(
            model_name='companyuser',
            name='company',
            field=models.ForeignKey(help_text='Virksomhed hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='users', to='esani_pantportal.company', verbose_name='Virksomhed'),
        ),
        migrations.AlterField(
            model_name='kioskuser',
            name='branch',
            field=models.ForeignKey(help_text='Butik hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='users', to='esani_pantportal.kiosk', verbose_name='Butik'),
        ),
        migrations.AlterField(
            model_name='refundmethod',
            name='branch',
            field=models.ForeignKey(blank=True, default=None, help_text='Afdeling hvor denne maskine står', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='refund_methods', to='esani_pantportal.companybranch', verbose_name='Afdeling'),
        ),
        migrations.AlterField(
            model_name='refundmethod',
            name='kiosk',
            field=models.ForeignKey(blank=True, default=None, help_text='Butik hvor denne maskine står', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='refund_methods', to='esani_pantportal.kiosk', verbose_name='Butik'),
        ),
        migrations.DeleteModel(
            name='PackagingRegistration',
        ),
        migrations.DeleteModel(
            name='ProductLine',
        ),
    ]
