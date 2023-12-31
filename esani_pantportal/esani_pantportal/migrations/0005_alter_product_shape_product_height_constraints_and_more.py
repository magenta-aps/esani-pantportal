# Generated by Django 4.2.2 on 2023-12-12 10:27
# Edited by Nick Janssen on 2023-12-13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esani_pantportal', '0004_update_product_database'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='shape',
            field=models.CharField(choices=[('F', 'Flaske'), ('D', 'Dåse'), ('A', 'Anden')], help_text='Kategori for emballagens form.', verbose_name='Form'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('height__gte', 85), ('height__lte', 380), ('shape', 'F')), models.Q(('height__gte', 80), ('height__lte', 200), ('shape', 'D')), models.Q(('height__gte', 80), ('height__lte', 380), ('shape', 'A')), _connector='OR'), name='height_constraints'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('diameter__gte', 50), ('diameter__lte', 130), ('shape', 'F')), models.Q(('diameter__gte', 50), ('diameter__lte', 100), ('shape', 'D')), models.Q(('diameter__gte', 50), ('diameter__lte', 130), ('shape', 'A')), _connector='OR'), name='diameter_constraints'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('capacity__gte', 150), ('capacity__lte', 3000), ('shape', 'F')), models.Q(('capacity__gte', 150), ('capacity__lte', 1000), ('shape', 'D')), models.Q(('capacity__gte', 150), ('capacity__lte', 3000), ('shape', 'A')), _connector='OR'), name='capacity_constraints'),
        ),
    ]
