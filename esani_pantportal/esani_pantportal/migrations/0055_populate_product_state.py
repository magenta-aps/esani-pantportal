from django.db import migrations
from django.db.models import Exists, OuterRef, Subquery

from esani_pantportal.models import ProductState


def populate_product_state(apps, schema_editor):
    Product = apps.get_model("esani_pantportal", "Product")
    Product.objects.filter(approved=True).update(state=ProductState.APPROVED)


def populate_product_history(apps, schema_editor):
    def fields(product, exclude=("has_history", "state")):
        return {
            k: v for k, v in product.__dict__.items()
            if not k.startswith("_") and k not in exclude
        }

    Product = apps.get_model("esani_pantportal", "Product")
    HistoricalProduct = apps.get_model("esani_pantportal", "HistoricalProduct")

    # Update history entries for products with a current history:
    HistoricalProduct.objects.filter(history_change_reason="Oprettet").update(state=ProductState.AWAITING_APPROVAL)
    HistoricalProduct.objects.filter(history_change_reason="Godkendt").update(state=ProductState.APPROVED)
    HistoricalProduct.objects.filter(history_change_reason="Gjort Inaktiv").update(state=ProductState.REJECTED)

    # Create history entries for products without current history:
    products = (
        Product.objects.order_by("id")
        .annotate(
            has_history=Exists(
                Subquery(
                    HistoricalProduct.objects.filter(id=OuterRef("id"))
                )
            )
        )
    )
    products_without_history = products.filter(has_history=False)
    creation_items = [
        HistoricalProduct(
            history_user=p.created_by,
            history_date=p.creation_date,
            history_change_reason="Oprettet",
            state=ProductState.AWAITING_APPROVAL,
            **fields(p),
        )
        for p in products_without_history.filter(creation_date__isnull=False)
    ]
    approval_items = [
        HistoricalProduct(
            history_date=p.approval_date,
            history_change_reason="Godkendt",
            state=ProductState.APPROVED,
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
