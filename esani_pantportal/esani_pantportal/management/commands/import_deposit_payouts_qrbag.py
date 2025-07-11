# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import re
from datetime import date, datetime, timedelta
from functools import cache
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Substr
from simple_history.utils import bulk_update_with_history

from esani_pantportal.clients.tomra.api import ConsumerSessionCollection, TomraAPI
from esani_pantportal.clients.tomra.data_models import ConsumerSession
from esani_pantportal.models import (
    AbstractCompany,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    ProductState,
    QRBag,
)


class Command(BaseCommand):
    help = "Import deposit payouts for 'QR bags' from Tomra 'consumer sessions' API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-date",
            help="Override default 'from date'",
        )
        parser.add_argument(
            "--to-date",
            help="Override default 'to date'",
        )

    def handle(self, *args, **options):
        from_date = self._get_previous_to_date(options["from_date"])
        to_date = self._get_todays_to_date(options["to_date"])

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
            if isinstance(datum.consumer_session, ConsumerSession)
            and not self._session_is_already_imported(datum.consumer_session.id)
        ]

    @cache
    def _session_is_already_imported(self, consumer_session_id: UUID) -> bool:
        return DepositPayoutItem.objects.filter(
            deposit_payout__source_type=DepositPayout.SOURCE_TYPE_API,
            consumer_session_id=consumer_session_id,
        ).exists()

    @transaction.atomic
    def _import_data(self, url, from_date, to_date, consumer_sessions):
        def get_qr_bag(consumer_session: ConsumerSession):
            consumer_identity = self._get_consumer_identity(consumer_session)
            if consumer_identity is not None:
                return self._get_qr_bag_from_qr(consumer_identity)

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

        deposit_payout_items = [
            DepositPayoutItem(
                deposit_payout=deposit_payout,
                qr_bag=get_qr_bag(consumer_session),
                company_branch=self._get_source(consumer_session, CompanyBranch),
                kiosk=self._get_source(consumer_session, Kiosk),
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
        DepositPayoutItem.objects.bulk_create(deposit_payout_items)

        # Update status of all related QR bags to `esani_optalt`
        qr_bags = QRBag.objects.filter(
            id__in=[
                deposit_payout_item.qr_bag.id
                for deposit_payout_item in deposit_payout_items
                if deposit_payout_item.qr_bag is not None
            ]
        )
        for qr_bag in qr_bags:
            qr_bag.status = "esani_optalt"
        bulk_update_with_history(qr_bags, QRBag, ["status"], batch_size=500)

    def _get_previous_to_date(self, val: str | None) -> date:
        if val is not None:
            return self._to_date(val)

        try:
            latest_api_import = DepositPayout.objects.filter(
                source_type=DepositPayout.SOURCE_TYPE_API
            ).latest("to_date")
        except DepositPayout.DoesNotExist:
            # Tomra API limits the available data to the latest 30 days.
            return date.today() - timedelta(days=30)
        else:
            return latest_api_import.to_date

    def _get_todays_to_date(self, val: str | None) -> date:
        if val is not None:
            return self._to_date(val)
        return date.today()

    def _to_date(self, val: str) -> date:
        return datetime.strptime(val, "%Y-%m-%d").date()

    def _to_datetime(self, val: date) -> datetime:
        return datetime(val.year, val.month, val.day)

    @cache
    def _get_qr_bag_from_qr(
        self,
        consumer_identity: str,
        qr_bag_model=QRBag,
    ) -> QRBag | None:
        """
        Find the matching `QRBag` instance for the given `consumer_identity`,
        and return either a `CompanyBranch`, a `Kiosk`, or None in case of no match.
        """

        long = 1 + settings.QR_ID_LENGTH + settings.QR_HASH_LENGTH
        short = 1 + settings.QR_ID_LENGTH

        qs = qr_bag_model.objects.annotate(
            qr_prefix=Substr("qr", 1, 1),
            qr_id=Substr("qr", 2, settings.QR_ID_LENGTH),
            qr_hash=Substr("qr", 2 + settings.QR_ID_LENGTH, settings.QR_HASH_LENGTH),
        )

        bag_qr = consumer_identity

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
            return None

        try:
            qr_bag = qs.get(lookup)
        except QRBag.DoesNotExist:
            self.stdout.write(f"No QRBag matches {bag_qr}")
        else:
            return qr_bag
        return None

    def _get_from_qr(
        self,
        consumer_identity: str,
        source_type: type[CompanyBranch] | type[Kiosk],
        qr_bag_model=QRBag,
    ) -> CompanyBranch | Kiosk | None:
        qr_bag = self._get_qr_bag_from_qr(consumer_identity, qr_bag_model=qr_bag_model)
        if qr_bag is None:
            return None
        if source_type is CompanyBranch:
            return qr_bag.company_branch
        elif source_type is Kiosk:
            return qr_bag.kiosk
        else:
            raise ValueError(f"Unknown source type {source_type=}")

    @cache
    def _get_direct(
        self,
        consumer_identity: str,
        source_type: type[CompanyBranch] | type[Kiosk],
    ) -> CompanyBranch | Kiosk | None:
        """
        Find the `CompanyBranch` or `Kiosk` whose external customer ID is encoded
        directly in the `consumer_identity` given.
        """

        # Look for strings starting with "8" or "9", followed by three zeroes, followed
        # by an external customer ID (6 digits, starting with either "1", "2" or "3".)
        pattern = re.compile(r"[8|9]000(?P<ext_id>[1|2|3]\d{5})")
        match = pattern.match(consumer_identity)

        if match:
            # Convert "200002" into "2-00002", etc.
            ext_id = match.group("ext_id")
            ext_id_with_separator = re.sub(r"(\d)(\d{5})", r"\g<1>-\g<2>", ext_id)

            # Try to look up object based on `ext_id_with_separator`
            try:
                obj = AbstractCompany.get_from_id(ext_id_with_separator)
            except ObjectDoesNotExist:
                self.stdout.write(
                    f"No matching object for external customer ID: "
                    f"{ext_id_with_separator}"
                )
            else:
                if isinstance(obj, (CompanyBranch, Kiosk)) and isinstance(
                    obj, source_type
                ):
                    return obj
                else:
                    self.stdout.write(
                        f"Unexpected match on `{obj.__class__.__name__}` "
                        f"(expected `{source_type.__name__}`): {ext_id_with_separator}"
                    )
        return None

    def _get_consumer_identity(self, consumer_session: ConsumerSession) -> str | None:
        return getattr(consumer_session.identity, "consumer_identity", None)

    def _get_source(
        self,
        consumer_session: ConsumerSession,
        source_type: type[CompanyBranch] | type[Kiosk],
    ) -> CompanyBranch | Kiosk | None:
        """
        Find the "source" of the given `consumer_session` - either a `CompanyBranch`,
        a `Kiosk`, or None.
        """
        consumer_identity = self._get_consumer_identity(consumer_session)
        if consumer_identity and isinstance(consumer_identity, str):
            # First, try looking for an external customer ID encoded directly in the
            # `consumer_identity`.
            source = self._get_direct(consumer_identity, source_type)
            if source is None:
                # Then, look for a `QRBag` matching `consumer_identity`
                source = self._get_from_qr(consumer_identity, source_type)
            return source
        else:
            self.stdout.write(
                f"No `identity` in {consumer_session.id} ({consumer_session.metadata=})"
            )
            return None

    @cache
    def _get_product_from_barcode(self, barcode) -> Product | None:
        try:
            product = Product.objects.exclude(state=ProductState.DELETED).get(
                barcode=barcode
            )
        except Product.DoesNotExist:
            return None
        else:
            return product

    def _get_qr_bag(self, consumer_identity, qr_bag_model=None):
        """
        Dummy implementation to keep the migration `0041_backfill_short_qr_codes`
        working.
        """
        return None
