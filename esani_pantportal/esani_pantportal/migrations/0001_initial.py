# Generated by Django 4.2.2 on 2023-10-12 13:56

from django.db import migrations, models
import django.db.models.deletion
import esani_pantportal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Firmanavn', max_length=255, verbose_name='Firmanavn')),
                ('cvr', models.PositiveIntegerField(help_text='CVR Nummer', unique=True, verbose_name='CVR Nummer')),
                ('address', models.CharField(help_text='Firmaets registrerede addresse', max_length=400, verbose_name='Addresse')),
                ('phone', models.PositiveIntegerField(help_text='Firmaets telefonnummer inkl. landekode', verbose_name='Telefonnummer')),
                ('permit_number', models.PositiveIntegerField(blank=True, help_text='Firmaets tilladelsesnummer for import af ethanolholdige drikkevarer', null=True, verbose_name='Tilladelsesnummer')),
            ],
        ),
        migrations.CreateModel(
            name='PackagingRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_number', models.PositiveIntegerField(help_text='Afgiftsanmeldelsesnummer', unique=True, verbose_name='Afgiftsanmeldelsesnummer')),
                ('date', models.DateField(auto_now_add=True, db_index=True, verbose_name='Dato')),
                ('recipient_company', models.ForeignKey(help_text='Firma, som skal modtage varerne og betale pant', on_delete=django.db.models.deletion.PROTECT, related_name='received_packaging', to='esani_pantportal.company', verbose_name='Varemodtager')),
                ('registration_company', models.ForeignKey(help_text='Firma ansvarligt for afgiftsanmeldelsen', on_delete=django.db.models.deletion.PROTECT, related_name='registered_packaging', to='esani_pantportal.company', verbose_name='Anmelder')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(help_text='Navn på det pågældende produkt', max_length=200, verbose_name='Produktnavn')),
                ('barcode', models.CharField(help_text='Stregkode for et indmeldt produkt', unique=True, validators=[esani_pantportal.models.validate_barcode_length, esani_pantportal.models.validate_digit], verbose_name='Stregkode')),
                ('refund_value', models.PositiveIntegerField(default=0, help_text='Pantværdi, angivet i eurocent (100=1Euro, 25=0.25Euro)', verbose_name='Pantværdi')),
                ('tax_group', models.PositiveIntegerField(help_text='Afgiftsgruppe', verbose_name='Afgiftsgruppe')),
                ('product_type', models.CharField(help_text='Vareart', max_length=200, verbose_name='Vareart')),
                ('approved', models.BooleanField(default=False, help_text='Produkt godkendt til pantsystemet af en ESANI medarbejder', verbose_name='Godkendt')),
                ('material_type', models.CharField(choices=[('P', 'PET'), ('A', 'Aluminium'), ('S', 'Stål'), ('G', 'Glas')], help_text='Materialetype', verbose_name='Materialetype')),
                ('height', models.PositiveIntegerField(help_text='Emballagens højde i Millimeter', verbose_name='Højde')),
                ('diameter', models.PositiveIntegerField(help_text='Emballagens diameter i Millimeter', verbose_name='Diameter')),
                ('weight', models.PositiveIntegerField(help_text='Tør/tom vægt af emballagen i Gram', verbose_name='Vægt')),
                ('capacity', models.PositiveIntegerField(help_text='Emballagens tiltænkte volumen i Milliliter', verbose_name='Volumenkapacitet')),
                ('shape', models.CharField(choices=[('F', 'Flaske'), ('A', 'Anden')], help_text='Kategori for emballagens form. Flasker er "Bottles", andre ting er "Other"', verbose_name='Form')),
            ],
            options={
                'ordering': ['product_name', 'barcode'],
                'permissions': [('approve_product', 'User is allowed to approve products awaiting registration')],
            },
        ),
        migrations.CreateModel(
            name='ProductLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(help_text='Styks pant-pligtig emballage importeret', verbose_name='Antal')),
                ('packaging_registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esani_pantportal.packagingregistration')),
                ('product', models.ForeignKey(help_text='Indmeldte produkt', on_delete=django.db.models.deletion.PROTECT, related_name='product_line', to='esani_pantportal.product', verbose_name='Produkt')),
            ],
        ),
        migrations.AddIndex(
            model_name='company',
            index=models.Index(fields=['name', 'cvr'], name='esani_pantp_name_aee5e3_idx'),
        ),
    ]
