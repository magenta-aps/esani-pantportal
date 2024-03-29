# Generated by Django 4.2.2 on 2024-02-20 14:55

from django.db import migrations

from esani_pantportal.management.commands.import_deposit_payouts_qrbag import Command
from esani_pantportal.models import DepositPayout


def backfill_deposit_payout_items(apps, schema_editor):
    DepositPayoutItem = apps.get_model("esani_pantportal", "DepositPayoutItem")
    QRBag = apps.get_model("esani_pantportal", "QRBag")

    # Find all objects which have not yet been linked to a QR bag, even though
    # they have a QR code.
    qs = (
        DepositPayoutItem.objects
        .filter(
            deposit_payout__source_type=DepositPayout.SOURCE_TYPE_API,
            consumer_identity__isnull=False,
            qr_bag__isnull=True,
        )
    )

    # Update all found objects by re-evaluating their QR code.
    command = Command()
    updated = 0
    skipped = 0
    for obj in qs:
        try:
            matching_qr_bag = command._get_qr_bag_from_qr(
                obj.consumer_identity,
                qr_bag_model=QRBag,
            )
        except QRBag.DoesNotExist:
            skipped += 1
        else:
            if matching_qr_bag:
                obj.qr_bag = matching_qr_bag
                obj.save()
                updated += 1
            else:
                skipped += 1

    print(f"Completed backfill: {updated=}, {skipped=}")


class Migration(migrations.Migration):

    dependencies = [
        ("esani_pantportal", "0045_depositpayoutitem_qr_bag"),
    ]

    operations = [
        migrations.RunPython(backfill_deposit_payout_items)
    ]
