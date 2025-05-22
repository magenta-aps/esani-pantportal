from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("esani_pantportal", "0069_populate_city_model"),
    ]

    operations = [
        # Remove old "city" varchar field from "company", "companybranch" and "kiosk"
        migrations.RemoveField(
            model_name="company",
            name="city",
        ),
        migrations.RemoveField(
            model_name="companybranch",
            name="city",
        ),
        migrations.RemoveField(
            model_name="kiosk",
            name="city",
        ),
        # Rename "city_fk" FK field to "city" on "company", "companybranch" and "kiosk"
        migrations.RenameField(
            model_name="company",
            old_name="city_fk",
            new_name="city",
        ),
        migrations.RenameField(
            model_name="companybranch",
            old_name="city_fk",
            new_name="city",
        ),
        migrations.RenameField(
            model_name="kiosk",
            old_name="city_fk",
            new_name="city",
        ),
        # Make "city" FK non-nullable on "company", "companybranch" and "kiosk"
        migrations.AlterField(
            model_name="company",
            name="city",
            field=models.ForeignKey(
                help_text="Butikken eller firmaets registrerede bynavn",
                on_delete=django.db.models.deletion.CASCADE,
                to="esani_pantportal.city",
                verbose_name="By",
            ),
        ),
        migrations.AlterField(
            model_name="companybranch",
            name="city",
            field=models.ForeignKey(
                help_text="Butikken eller firmaets registrerede bynavn",
                on_delete=django.db.models.deletion.CASCADE,
                to="esani_pantportal.city",
                verbose_name="By",
            ),
        ),
        migrations.AlterField(
            model_name="kiosk",
            name="city",
            field=models.ForeignKey(
                help_text="Butikken eller firmaets registrerede bynavn",
                on_delete=django.db.models.deletion.CASCADE,
                to="esani_pantportal.city",
                verbose_name="By",
            ),
        ),
    ]
