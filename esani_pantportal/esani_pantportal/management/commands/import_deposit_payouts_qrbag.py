# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date, datetime, timedelta
from functools import cache
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Substr

from esani_pantportal.clients.tomra.api import ConsumerSessionCollection, TomraAPI
from esani_pantportal.clients.tomra.data_models import ConsumerSession
from esani_pantportal.models import (
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    QRBag,
)


class Command(BaseCommand):
    help = "Import deposit payouts for 'QR bags' from Tomra 'consumer sessions' API"

    num_days = 1  # How many days of data to fetch from Tomra

    def handle(self, **kwargs):
        from_date = self._get_previous_to_date()
        to_date = self._get_todays_to_date(from_date)

        api = TomraAPI.from_settings()

        self.stdout.write(f"Retrieving consumer sessions, {from_date=}, {to_date=} ...")
        consumer_sessions = api.get_consumer_sessions(
            self._to_datetime(from_date),
            self._to_datetime(to_date),
        )
        self.stdout.write(
            f"Retrieved {len(consumer_sessions.data)} consumer sessions "
            f"({from_date=}, {to_date=})"
        )

        consumer_sessions_filtered = self._filter_consumer_sessions(consumer_sessions)
        self.stdout.write(
            f"{len(consumer_sessions_filtered)} consumer sessions are valid "
            f"'bag sessions' that have not yet been imported."
        )

        if consumer_sessions_filtered:
            self.stdout.write("Importing ...")
            self._import_data(
                consumer_sessions.url,
                from_date,
                to_date,
                consumer_sessions_filtered,
            )
            self.stdout.write("Done.")
        else:
            self.stdout.write("Not importing anything.")

    def _filter_consumer_sessions(
        self, consumer_sessions: ConsumerSessionCollection
    ) -> list[ConsumerSession]:
        return [
            datum.consumer_session
            for datum in consumer_sessions.data
            if self._all_items_have_barcode(datum.consumer_session.items)
            and not self._session_is_already_imported(datum.consumer_session.id)
        ]

    def _all_items_have_barcode(self, items) -> bool:
        return all(it.product_code is not None for it in items) if items else False

    @cache
    def _session_is_already_imported(self, consumer_session_id: UUID) -> bool:
        return DepositPayoutItem.objects.filter(
            deposit_payout__source_type=DepositPayout.SOURCE_TYPE_API,
            consumer_session_id=consumer_session_id,
        ).exists()

    @transaction.atomic
    def _import_data(self, url, from_date, to_date, consumer_sessions):
        deposit_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_API,
            source_identifier=url,
            from_date=from_date,
            to_date=to_date,
            item_count=len(
                [
                    item
                    for consumer_session in consumer_sessions
                    for item in consumer_session.items
                ]
            ),
        )
        DepositPayoutItem.objects.bulk_create(
            [
                DepositPayoutItem(
                    deposit_payout=deposit_payout,
                    company_branch=self._get_company_branch(consumer_session),
                    kiosk=self._get_kiosk(consumer_session),
                    product=self._get_product_from_barcode(item.product_code),
                    barcode=item.product_code,
                    count=item.count,
                    location_id=consumer_session.metadata.location.customer_id,
                    rvm_serial=consumer_session.metadata.rvm.serial_number,
                    date=consumer_session.started_at,
                    consumer_session_id=consumer_session.id,
                    consumer_identity=self._get_consumer_identity(consumer_session),
                )
                for consumer_session in consumer_sessions
                for item in consumer_session.items
            ]
        )

    def _get_previous_to_date(self) -> date:
        try:
            latest_api_import = DepositPayout.objects.filter(
                source_type=DepositPayout.SOURCE_TYPE_API
            ).latest("to_date")
        except DepositPayout.DoesNotExist:
            return date(2024, 1, 1)
        else:
            return latest_api_import.to_date

    def _get_todays_to_date(self, from_date: date) -> date:
        return from_date + timedelta(days=self.num_days)

    def _to_datetime(self, val: date) -> datetime:
        return datetime(val.year, val.month, val.day)

    @cache
    def _get_qr_bag(self, bag_qr, qr_bag_model=QRBag) -> QRBag | None:
        long = 1 + settings.QR_ID_LENGTH + settings.QR_HASH_LENGTH
        short = 1 + settings.QR_ID_LENGTH

        qs = qr_bag_model.objects.annotate(
            qr_prefix=Substr("qr", 1, 1),
            qr_id=Substr("qr", 2, settings.QR_ID_LENGTH),
            qr_hash=Substr("qr", 2 + settings.QR_ID_LENGTH, settings.QR_HASH_LENGTH),
        )

        if len(bag_qr) == long:
            # 18-digit QR code (prefix + ID + hash.)
            # Exact match on entire QR.
            lookup = Q(qr=bag_qr)
        elif len(bag_qr) == short:
            # 10-digit QR code (prefix + ID.)
            # Exact match on QR prefix and ID only.
            lookup = Q(qr_prefix=bag_qr[0], qr_id=bag_qr[1:])
        elif len(bag_qr) == settings.QR_ID_LENGTH:
            # 9-digit QR code (ID only.)
            # Exact match on QR ID.
            lookup = Q(qr_id=bag_qr)
        else:
            # The provided QR code is neither 18, 10 or 9 digits long.
            self.stdout.write(
                f"Not looking up `QRBag` for code of unexpected length: "
                f"{bag_qr=} (length={len(bag_qr)})"
            )
            return

        try:
            return qs.get(lookup)
        except QRBag.DoesNotExist:
            self.stdout.write(f"No QRBag matches {bag_qr}")

    def _get_consumer_identity(self, consumer_session: ConsumerSession):
        try:
            return consumer_session.identity.consumer_identity
        except AttributeError:
            # 'NoneType' object has no attribute 'consumer_identity'
            pass

    def _get_company_branch(
        self, consumer_session: ConsumerSession
    ) -> CompanyBranch | None:
        try:
            qr_bag = self._get_qr_bag(consumer_session.identity.consumer_identity)
        except AttributeError:
            # 'NoneType' object has no attribute 'consumer_identity'
            self.stdout.write(
                f"No `identity` in {consumer_session.id} ({consumer_session.metadata=}"
            )
        else:
            if qr_bag:
                return qr_bag.company_branch

    def _get_kiosk(self, consumer_session: ConsumerSession) -> Kiosk | None:
        try:
            qr_bag = self._get_qr_bag(consumer_session.identity.consumer_identity)
        except AttributeError:
            # 'NoneType' object has no attribute 'consumer_identity'
            self.stdout.write(
                f"No `identity` in {consumer_session.id} ({consumer_session.metadata=}"
            )
        else:
            if qr_bag:
                return qr_bag.kiosk

    @cache
    def _get_product_from_barcode(self, barcode) -> Product | None:
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            return None
        else:
            return product
