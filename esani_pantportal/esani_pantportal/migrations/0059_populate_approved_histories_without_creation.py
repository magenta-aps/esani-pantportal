from django.contrib.postgres.aggregates import ArrayAgg
from django.db import migrations

from esani_pantportal.models import ProductState


def populate_approved_only_histories(apps, schema_editor) -> None:
    # Add "awaiting approval" history entry to products which have only an "approved"
    # history entry:

    def fields(product, exclude=("state",)):
        return {
            k: v for k, v in product.__dict__.items()
            if not k.startswith("_") and k not in exclude
        }

    Product = apps.get_model("esani_pantportal", "Product")
    HistoricalProduct = apps.get_model("esani_pantportal", "HistoricalProduct")

    has_only_approved = (
        Product.objects.order_by("id")
        .annotate(_state_agg=ArrayAgg("history_entries__state", distinct=True))
        .filter(_state_agg=[ProductState.APPROVED])
    )
    creation_items = [
        HistoricalProduct(
            history_relation_id=p.id,
            history_date=(
                HistoricalProduct.objects
                .filter(id=p.id, state=ProductState.APPROVED)
                .order_by("history_date")
                .first()
                .history_date
            ),
            history_change_reason="Oprettet",
            state=ProductState.AWAITING_APPROVAL,
            **fields(p),
        )
        for p in has_only_approved
    ]
    HistoricalProduct.objects.bulk_create(creation_items)


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0058_historicalproduct_rejection_product_rejection"),
    ]

    operations = [
        migrations.RunPython(populate_approved_only_histories),
    ]
