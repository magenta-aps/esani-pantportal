from django.db import migrations
from django.db.models import Exists, OuterRef, Subquery

from esani_pantportal.models import ProductState


def populate_product_state(apps, schema_editor):
    Product = apps.get_model("esani_pantportal", "Product")
    Product.objects.filter(approved=True).update(state=ProductState.APPROVED)


def populate_product_history(apps, schema_editor):
    def fields(product, exclude=("has_history",)):
        return {
            k: v for k, v in product.__dict__.items()
            if not k.startswith("_") and k not in exclude
        }

    Product = apps.get_model("esani_pantportal", "Product")
    HistoricalProduct = apps.get_model("esani_pantportal", "HistoricalProduct")

    products_without_history = (
        Product.objects.annotate(
            has_history=Exists(
                Subquery(
                    HistoricalProduct.objects.filter(id=OuterRef("id"))
                )
            )
        )
        .filter(has_history=False)
        .order_by("id")
    )

    creation_items = [
        HistoricalProduct(
            history_user=p.created_by,
            history_date=p.creation_date,
            history_change_reason="Oprettet",
            **fields(p),
        )
        for p in products_without_history.filter(creation_date__isnull=False)
    ]

    approval_items = [
        HistoricalProduct(
            history_date=p.approval_date,
            history_change_reason="Godkendt",
            **fields(p),
        )
        for p in products_without_history.filter(approved=True, approval_date__isnull=False)
    ]

    HistoricalProduct.objects.bulk_create(creation_items + approval_items)


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0054_historicalproduct_state_product_state_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_product_state),
        migrations.RunPython(populate_product_history),
    ]
