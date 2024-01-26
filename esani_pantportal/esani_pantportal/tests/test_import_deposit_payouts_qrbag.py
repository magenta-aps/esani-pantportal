# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import uuid
from datetime import date, datetime
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from esani_pantportal.clients.tomra.api import ConsumerSessionCollection, TomraAPI
from esani_pantportal.clients.tomra.data_models import (
    ConsumerSession,
    Datum,
    Identity,
    Item1,
    Location,
    Metadata,
    Rvm,
)
from esani_pantportal.management.commands.import_deposit_payouts_qrbag import Command
from esani_pantportal.models import (
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    QRBag,
)


class TestImportDepositPayoutsQRBag(TestCase):
    kiosk_cvr = 1234
    bag_qr = "12345678"
    product_barcode_1 = "1122"
    product_count_1 = 10
    product_barcode_2 = "2233"
    product_count_2 = 20
    location_customer_id = 1000
    rvm_serial_number = 2000
    consumer_session_id = uuid.uuid4()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Add `Kiosk` object
        kiosk, _ = Kiosk.objects.update_or_create(cvr=cls.kiosk_cvr)

        # Add `QRBag` object
        QRBag.objects.update_or_create(qr=cls.bag_qr, kiosk=kiosk)

        # Add `Product` objects
        defaults = {
            "height": 250,
            "diameter": 50,
            "weight": 20,
            "capacity": 330,
            "shape": "F",
        }
        cls.product_1, _ = Product.objects.update_or_create(
            product_name="Foo",
            barcode=cls.product_barcode_1,
            defaults=defaults,
        )
        cls.product_2, _ = Product.objects.update_or_create(
            product_name="Bar",
            barcode=cls.product_barcode_2,
            defaults=defaults,
        )

    def test_import_creates_expected_objects(self):
        # Arrange
        data = [
            # First datum uses a consumer identity matching out QR bag, and contains
            # two items both with a known product barcode.
            Datum(
                consumer_session=ConsumerSession(
                    id=self.consumer_session_id,
                    identity=Identity(consumer_identity=self.bag_qr),
                    metadata=Metadata(
                        location=Location(customer_id=self.location_customer_id),
                        rvm=Rvm(serial_number=self.rvm_serial_number),
                    ),
                    started_at=datetime(2020, 1, 1, 12, 0),
                    items=[
                        Item1(
                            product_code=self.product_barcode_1,
                            count=self.product_count_1,
                        ),
                        Item1(
                            product_code=self.product_barcode_2,
                            count=self.product_count_2,
                        ),
                    ],
                ),
            ),
            # Second datum uses an unknown consumer identity and contains one item with
            # an unknown product barcode.
            Datum(
                consumer_session=ConsumerSession(
                    id=self.consumer_session_id,
                    identity=Identity(consumer_identity="unknown_bag_qr"),
                    metadata=Metadata(
                        location=Location(customer_id=self.location_customer_id),
                        rvm=Rvm(serial_number=self.rvm_serial_number),
                    ),
                    started_at=datetime(2020, 1, 1, 12, 0),
                    items=[
                        Item1(
                            product_code="product_code",
                            count=0,
                        ),
                    ],
                ),
            ),
        ]

        with patch(
            "esani_pantportal.management.commands.import_deposit_payouts_qrbag."
            "TomraAPI.from_settings",
            return_value=self._get_mock_api(data),
        ):
            # Act: run command twice on same input to ensure idempotency
            buf = StringIO()
            call_command(Command(), stdout=buf, stderr=buf)
            call_command(Command(), stdout=buf, stderr=buf)

            # Assert: check the output
            self.assertIn("Importing ...", buf.getvalue())
            self.assertIn("Not importing anything", buf.getvalue())

            # Assert: check the `DepositPayout`/`DepositPayoutItem` objects
            self._assert_objects_created()

    def _get_mock_api(self, data=None):
        mock_api = Mock(spec=TomraAPI)
        mock_api.get_consumer_sessions = Mock(
            return_value=ConsumerSessionCollection(
                url="url",
                from_date=datetime(2020, 1, 1),
                to_date=datetime(2020, 2, 1),
                data=[] if data is None else data,
            ),
        )
        return mock_api

    def _assert_objects_created(self):
        # Assert we create exactly one `DepositPayout` (even though we run the same
        # import twice.)
        self.assertQuerySetEqual(
            DepositPayout.objects.all(),
            [(DepositPayout.SOURCE_TYPE_API, "url", 2)],
            transform=lambda obj: (
                obj.source_type,
                obj.source_identifier,
                obj.item_count,
            ),
            ordered=False,
        )
        # Assert we create exactly two `DepositPayoutItems` (even though we run the
        # same import twice.) Check that the fields are set as expected.
        self.assertQuerySetEqual(
            DepositPayoutItem.objects.all(),
            [
                (
                    self.kiosk_cvr,
                    self.product_1,
                    self.product_barcode_1,
                    self.product_count_1,
                    self.rvm_serial_number,
                    date(2020, 1, 1),
                    self.consumer_session_id,
                    self.bag_qr,
                ),
                (
                    self.kiosk_cvr,
                    self.product_2,
                    self.product_barcode_2,
                    self.product_count_2,
                    self.rvm_serial_number,
                    date(2020, 1, 1),
                    self.consumer_session_id,
                    self.bag_qr,
                ),
            ],
            transform=lambda obj: (
                obj.kiosk.cvr,
                obj.product,
                obj.barcode,
                obj.count,
                obj.rvm_serial,
                obj.date,
                obj.consumer_session_id,
                obj.consumer_identity,
            ),
            ordered=False,
        )

    def test_get_product_from_barcode_returns_none_on_unknown_barcode(self):
        # Arrange
        cmd = Command()
        # Act and assert
        self.assertIsNone(cmd._get_product_from_barcode("unknown_barcode"))
