# Generated by Django 4.2.2 on 2023-11-28 14:18

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import esani_pantportal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('user_type', models.PositiveSmallIntegerField(choices=[(1, 'Esanibruger'), (2, 'Butiksbruger'), (3, 'Virksomhedsbruger'), (4, 'Kioskbruger')])),
                ('phone', models.CharField(help_text='Brugerens telefonnummer inkl. landekode', max_length=30, verbose_name='Telefonnummer')),
                ('approved', models.BooleanField(choices=[(True, 'Ja'), (False, 'Nej')], default=False, help_text='Bruger godkendt af en ESANI medarbejder', verbose_name='Godkendt')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'ordering': ['username'],
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Firma eller butiksnavn', max_length=255, verbose_name='Navn')),
                ('address', models.CharField(help_text='Butikken eller firmaets registrerede adresse', max_length=255, verbose_name='Adresse')),
                ('postal_code', models.CharField(help_text='Butikken eller firmaets registrerede postnummer', max_length=10, verbose_name='Postnr.')),
                ('municipality', models.CharField(help_text='Butikken eller firmaets registrerede kommunenavn', max_length=255, verbose_name='Kommune')),
                ('city', models.CharField(help_text='Butikken eller firmaets registrerede bynavn', max_length=255, verbose_name='By')),
                ('phone', models.CharField(help_text='Butikken eller firmaets telefonnummer inkl. landekode', max_length=30, verbose_name='Telefonnummer')),
                ('registration_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto reg. nr. (valgfri)', null=True, verbose_name='reg. nr.')),
                ('account_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto nr. (valgfri)', null=True, verbose_name='konto nr.')),
                ('invoice_mail', models.EmailField(blank=True, default=None, help_text='Mail adresse som faktura skal sendes til (valgfri)', max_length=254, null=True, verbose_name='Faktura mail')),
                ('esani_customer_id', models.PositiveIntegerField(blank=True, default=None, help_text='Butikkens kontonummer hos ESANI (udfyldes af ESANI)', null=True, verbose_name='Konto')),
                ('cvr', models.PositiveIntegerField(help_text='CVR Nummer', unique=True, verbose_name='CVR Nummer')),
                ('permit_number', models.PositiveIntegerField(blank=True, help_text='Firmaets tilladelsesnummer for import af ethanolholdige drikkevarer (valgfri)', null=True, verbose_name='Tilladelsesnummer')),
                ('company_type', models.CharField(choices=[('E', 'Eksportør'), ('A', 'Andet')], help_text='Virksomhedstype', verbose_name='Virksomhedstype')),
                ('country', models.CharField(help_text='Butikken eller firmaets registrerede landenavn', max_length=255, verbose_name='Land')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CompanyBranch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Firma eller butiksnavn', max_length=255, verbose_name='Navn')),
                ('address', models.CharField(help_text='Butikken eller firmaets registrerede adresse', max_length=255, verbose_name='Adresse')),
                ('postal_code', models.CharField(help_text='Butikken eller firmaets registrerede postnummer', max_length=10, verbose_name='Postnr.')),
                ('municipality', models.CharField(help_text='Butikken eller firmaets registrerede kommunenavn', max_length=255, verbose_name='Kommune')),
                ('city', models.CharField(help_text='Butikken eller firmaets registrerede bynavn', max_length=255, verbose_name='By')),
                ('phone', models.CharField(help_text='Butikken eller firmaets telefonnummer inkl. landekode', max_length=30, verbose_name='Telefonnummer')),
                ('registration_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto reg. nr. (valgfri)', null=True, verbose_name='reg. nr.')),
                ('account_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto nr. (valgfri)', null=True, verbose_name='konto nr.')),
                ('invoice_mail', models.EmailField(blank=True, default=None, help_text='Mail adresse som faktura skal sendes til (valgfri)', max_length=254, null=True, verbose_name='Faktura mail')),
                ('esani_customer_id', models.PositiveIntegerField(blank=True, default=None, help_text='Butikkens kontonummer hos ESANI (udfyldes af ESANI)', null=True, verbose_name='Konto')),
                ('location_id', models.PositiveIntegerField(blank=True, default=None, help_text='Butikkens lokation ID (valgfri)', null=True, verbose_name='LokationsID')),
                ('customer_id', models.PositiveIntegerField(blank=True, help_text='Butikkens kundenummer hos Tomra (valgfri)', null=True, verbose_name='Kundenummer')),
                ('branch_type', models.CharField(choices=[('D', 'Detail'), ('H', 'Hotel/Restauration/Bar'), ('F', 'Forening'), ('A', 'Andet')], help_text='Branche-type', verbose_name='Branche')),
                ('company', models.ForeignKey(help_text='Virksomhed som denne butik tilhører', on_delete=django.db.models.deletion.PROTECT, related_name='company', to='esani_pantportal.company', verbose_name='Virksomhed')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Kiosk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Firma eller butiksnavn', max_length=255, verbose_name='Navn')),
                ('address', models.CharField(help_text='Butikken eller firmaets registrerede adresse', max_length=255, verbose_name='Adresse')),
                ('postal_code', models.CharField(help_text='Butikken eller firmaets registrerede postnummer', max_length=10, verbose_name='Postnr.')),
                ('municipality', models.CharField(help_text='Butikken eller firmaets registrerede kommunenavn', max_length=255, verbose_name='Kommune')),
                ('city', models.CharField(help_text='Butikken eller firmaets registrerede bynavn', max_length=255, verbose_name='By')),
                ('phone', models.CharField(help_text='Butikken eller firmaets telefonnummer inkl. landekode', max_length=30, verbose_name='Telefonnummer')),
                ('registration_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto reg. nr. (valgfri)', null=True, verbose_name='reg. nr.')),
                ('account_number', models.PositiveIntegerField(blank=True, default=None, help_text='Pant konto nr. (valgfri)', null=True, verbose_name='konto nr.')),
                ('invoice_mail', models.EmailField(blank=True, default=None, help_text='Mail adresse som faktura skal sendes til (valgfri)', max_length=254, null=True, verbose_name='Faktura mail')),
                ('esani_customer_id', models.PositiveIntegerField(blank=True, default=None, help_text='Butikkens kontonummer hos ESANI (udfyldes af ESANI)', null=True, verbose_name='Konto')),
                ('location_id', models.PositiveIntegerField(blank=True, default=None, help_text='Butikkens lokation ID (valgfri)', null=True, verbose_name='LokationsID')),
                ('customer_id', models.PositiveIntegerField(blank=True, help_text='Butikkens kundenummer hos Tomra (valgfri)', null=True, verbose_name='Kundenummer')),
                ('branch_type', models.CharField(choices=[('D', 'Detail'), ('H', 'Hotel/Restauration/Bar'), ('F', 'Forening'), ('A', 'Andet')], help_text='Branche-type', verbose_name='Branche')),
                ('cvr', models.PositiveIntegerField(help_text='CVR Nummer', unique=True, verbose_name='CVR Nummer')),
                ('permit_number', models.PositiveIntegerField(blank=True, help_text='Butikkens tilladelsesnummer for import af ethanolholdige drikkevarer (valgfri)', null=True, verbose_name='Tilladelsesnummer')),
            ],
            options={
                'abstract': False,
            },
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
                ('refund_value', models.PositiveIntegerField(default=200, help_text='Pantværdi, angivet i øre (100=1DKK, 25=0.25DKK)', verbose_name='Pantværdi')),
                ('approved', models.BooleanField(default=False, help_text='Produkt godkendt til pantsystemet af en ESANI medarbejder', verbose_name='Godkendt')),
                ('material', models.CharField(choices=[('P', 'PET'), ('A', 'Aluminium'), ('S', 'Stål'), ('G', 'Glas')], help_text='Kategori for emballagens materiale.', verbose_name='Materiale')),
                ('height', models.PositiveIntegerField(help_text='Emballagens højde i millimeter', verbose_name='Højde')),
                ('diameter', models.PositiveIntegerField(help_text='Emballagens diameter i millimeter', verbose_name='Diameter')),
                ('weight', models.PositiveIntegerField(help_text='Tør/tom vægt af emballagen i gram', verbose_name='Vægt')),
                ('capacity', models.PositiveIntegerField(help_text='Emballagens volumen i milliliter', verbose_name='Volumen')),
                ('shape', models.CharField(choices=[('F', 'Flaske'), ('A', 'Anden')], help_text='Kategori for emballagens form.', verbose_name='Form')),
                ('danish', models.CharField(choices=[('J', 'Ja'), ('N', 'Nej'), ('U', 'Ukendt')], default='U', help_text='Der er Dansk pant på dette produkt', verbose_name='Dansk pant')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to=settings.AUTH_USER_MODEL, verbose_name='Oprettet af')),
            ],
            options={
                'ordering': ['product_name', 'barcode'],
                'permissions': [('approve_product', 'User is allowed to approve products awaiting registration')],
            },
        ),
        migrations.CreateModel(
            name='QRCodeGenerator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(default=0, help_text='Antal QR-koder genereret indtil nu', verbose_name='Antal QR-koder')),
                ('name', models.CharField(help_text='Navn på denne serie af QR-koder', max_length=200, unique=True, verbose_name='Navn')),
                ('prefix', models.PositiveIntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='EsaniUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'esaniuser',
                'verbose_name_plural': 'esaniusers',
                'abstract': False,
            },
            bases=('esani_pantportal.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='RefundMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('compensation', models.PositiveIntegerField(default=0, help_text='Håndterings-godtgørelse, angivet i øre (100=1DKK, 25=0.25DKK)', verbose_name='Håndterings-godtgørelse')),
                ('serial_number', models.CharField(blank=True, help_text='Maskinens serienummer', null=True, verbose_name='Serienummer')),
                ('method', models.CharField(choices=[('K', 'Flaskeautomat m/komprimator'), ('S', 'Flaskeautomat m/sikkerhedscontainer'), ('SK', 'Flaskeautomat m/komprimator m/sikkerhedscontainer'), ('S', 'Sække'), ('M', 'Manuel sortering'), ('A', 'Anden')], help_text='Måden at pant bliver registreret på', verbose_name='Pantmetode')),
                ('branch', models.ForeignKey(blank=True, default=None, help_text='Kæde hvor denne maskine står', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='kæde', to='esani_pantportal.companybranch', verbose_name='Kæde')),
                ('kiosk', models.ForeignKey(blank=True, default=None, help_text='Butik hvor denne maskine står', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='kiosk', to='esani_pantportal.kiosk', verbose_name='Butik')),
            ],
        ),
        migrations.CreateModel(
            name='QRCodeInterval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.PositiveIntegerField()),
                ('increment', models.PositiveIntegerField()),
                ('salt', models.CharField(max_length=200)),
                ('generator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intervals', to='esani_pantportal.qrcodegenerator')),
            ],
            options={
                'ordering': ['start'],
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
        migrations.CreateModel(
            name='KioskUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('branch', models.ForeignKey(help_text='Butik hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='user_kiosk', to='esani_pantportal.kiosk', verbose_name='Butik')),
            ],
            options={
                'verbose_name': 'kioskuser',
                'verbose_name_plural': 'kioskusers',
                'abstract': False,
            },
            bases=('esani_pantportal.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='CompanyUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(help_text='Virksomhed hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='user_company', to='esani_pantportal.company', verbose_name='Virksomhed')),
            ],
            options={
                'verbose_name': 'companyuser',
                'verbose_name_plural': 'companyusers',
                'abstract': False,
            },
            bases=('esani_pantportal.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='BranchUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('branch', models.ForeignKey(help_text='Butik hvor denne bruger arbejder', on_delete=django.db.models.deletion.PROTECT, related_name='user_branch', to='esani_pantportal.companybranch', verbose_name='Butik')),
            ],
            options={
                'verbose_name': 'branchuser',
                'verbose_name_plural': 'branchusers',
                'abstract': False,
            },
            bases=('esani_pantportal.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
