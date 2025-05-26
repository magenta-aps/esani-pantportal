from django.db import migrations


CITY_NAMES = {
    "Aappilattoq (Avannaata)": [],
    "Aasiaat": [],
    "Akunnaaq": [],
    "Alluitsup Paa": [],
    "Ammassivik": [],
    "Appilattoq": [],
    "Arsuk": [],
    "Atammik": [],
    "Danmark": ["Aalborg Øst", "Albertslund", "Fur", "Give", "Ishøj", "Kolding"],
    "Eqalugaaarsuit": [],
    "Eqalugaarsuit": [],
    "Igaliku": [],
    "Iginniarfik": [],
    "Ikamiut": [],
    "Ikerasaarsuk": [],
    "Ikerasak": [],
    "Ilimanaq": [],
    "Ilulissat": ["Ilulissat", "illussat", "ilulissat", "Ilulissat", "ILULISSAT"],
    "Innaarsuit": [],
    "Isertoq": [],
    "Itilleq": [],
    "Ittoqqortoormiit": [],
    "Kangaamiut": [],
    "Kangaatsiaq": [],
    "Kangerluk": [],
    "Kangerlussaq": [],
    "Kangerlussuaq": [],
    "Kangilinnguit": [],
    "Kapisillit": [],
    "Kisisuarsuit": [],
    "Kitsissuarsuit": [],
    "Kullorsuaq": [],
    "Kulusuk": [],
    "Kuumiut": [],
    "Kuummiut": [],
    "Maniitsoq": [],
    "Naajaat": [],
    "Nanortalik": [],
    "Napasoq": [],
    "Narsaq": [],
    "Narsarmijit": [],
    "Narsarsuaq": [],
    "Nerlerit Inaat": [],
    "Niaqornat": [],
    "Nutaarmiut": [],
    "Nutsiaq": [],
    "Nuugaatsiaq": [],
    "Nuuk": ["Nuuk", "nuuk"],
    "Nuussuaq": [],
    "Oqaatsut": [],
    "Paamiut": [],
    "Qaanaaq": [],
    "Qaarsiarsuk": [],
    "Qaarsut": [],
    "Qaqortoq": [],
    "Qasigiannguit": [],
    "Qassiarsuk": [],
    "Qassimiut": [],
    "Qeqertaq": [],
    "Qeqertarsiatsiaat": [],
    "Qeqertarsuaq": [],
    "Qeqertarsuatsiaat": [],
    "Qeqertat": [],
    "Qernertunnguit": [],
    "Saarloq": [],
    "Saattut": [],
    "Saqqaq": [],
    "Savissivik": [],
    "Siorapaluk": [],
    "Sisimiut": ["Sisimiut", "Sisimut"],
    "Tasiilaq": [],
    "Tasiusaq": [],
    "Tiniteqilaaq": [],
    "Tussaaq": [],
    "Ukkusissat": [],
    "Upernavik Kujalleq": [],
    "Upernavik": [],
    "Uummannaq": [],
}


def populate_city_model(apps, schema_editor):
    City = apps.get_model("esani_pantportal", "City")
    City.objects.bulk_create([City(name=name) for name in CITY_NAMES])


def populate_city_fk(apps, schema_editor):
    City = apps.get_model("esani_pantportal", "City")
    Company = apps.get_model("esani_pantportal", "Company")
    CompanyBranch = apps.get_model("esani_pantportal", "CompanyBranch")
    Kiosk = apps.get_model("esani_pantportal", "Kiosk")

    for name, aliases in CITY_NAMES.items():
        city_fk = City.objects.get(name=name)
        for model in (Company, CompanyBranch, Kiosk):
            if aliases:
                qs = model.objects.filter(city__in=aliases)
            else:
                qs = model.objects.filter(city=name)
            qs.update(city_fk=city_fk)


class Migration(migrations.Migration):
    dependencies = [
        (
            "esani_pantportal",
            "0068_city_company_city_fk_companybranch_city_fk_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(populate_city_model),
        migrations.RunPython(populate_city_fk),
    ]
