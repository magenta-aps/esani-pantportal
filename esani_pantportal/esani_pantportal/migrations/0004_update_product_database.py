# Written by Nick Janssen on 2023-12-13

from django.db import migrations
from django.conf import settings


def migrate_product_model(apps, schema_editor):
    Product = apps.get_model("esani_pantportal", "Product")
    constraints = settings.PRODUCT_CONSTRAINTS

    for product in Product.objects.filter(shape=""):
        product.shape = "A"
        print(f"Updating {product}[shape]=A")
        product.save()

    for attr, shapedict in constraints.items():
        for shape, [minv, maxv] in shapedict.items():

            for product in Product.objects.filter(
                **{attr + "__lt": minv, "shape": shape}
            ):
                setattr(product, attr, minv)
                print(f"Updating {product}[{attr}]={minv}")
                product.save()

            for product in Product.objects.filter(
                **{attr + "__gt": maxv, "shape": shape}
            ):
                setattr(product, attr, maxv)
                print(f"Updating {product}[{attr}]={maxv}")
                product.save()


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0003_remove_productline_packaging_registration_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_product_model),
    ]
