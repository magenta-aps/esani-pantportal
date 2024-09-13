# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import uuid
from datetime import date, datetime, timedelta
from io import StringIO
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from unittest_parametrize import ParametrizedTestCase, parametrize

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
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    QRBag,
)

EXAMPLE_QR_ID = "0" * settings.QR_ID_LENGTH


class TestImportDepositPayoutsQRBag(ParametrizedTestCase, TestCase):
    maxDiff = None

    kiosk_cvr = 1234
    bag_qr = "0123456789deadbeef"
    product_barcode_1 = "1122"
    product_count_1 = 10
    product_barcode_2 = "2233"
    product_count_2 = 20
    location_customer_id = 1000
    rvm_serial_number = 2000
    consumer_session_id = uuid.uuid4()

    _mock_api_path = (
        "esani_pantportal.management.commands.import_deposit_payouts_qrbag."
        "TomraAPI.from_settings"
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Add `Kiosk` object
        cls.kiosk, _ = Kiosk.objects.update_or_create(cvr=cls.kiosk_cvr)

        # Add `Company` and `CompanyBranch` objects
        cls.company, _ = Company.objects.update_or_create(cvr=2345)
        cls.company_branch, _ = CompanyBranch.objects.update_or_create(
            company=cls.company,
        )

        # Add `QRBag` object
        cls.qr_bag, _ = QRBag.objects.update_or_create(qr=cls.bag_qr, kiosk=cls.kiosk)

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

        cls.consumer_identity_ext_id = f"80003{cls.kiosk.id:05}"

    def test_handle_processes_to_and_from_args(self):
        # Arrange
        mock_api = self._get_mock_api()
        with patch(self._mock_api_path, return_value=mock_api):
            buf = StringIO()
            # Act
            call_command(
                Command(),
                stdout=buf,
                stderr=buf,
                from_date="2020-01-01",
                to_date="2020-01-31",
            )
            # Assert
            mock_api.get_consumer_sessions.assert_called_once_with(
                datetime(2020, 1, 1),
                datetime(2020, 1, 31),
            )

    def test_import_creates_expected_objects(self):
        # Arrange
        data = [
            # First datum uses a consumer identity matching our QR bag, and contains
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
            # Third datum uses a 10-digit consumer identity containing an
            # external customer ID.
            Datum(
                consumer_session=ConsumerSession(
                    id=self.consumer_session_id,
                    identity=Identity(
                        consumer_identity=self.consumer_identity_ext_id,
                    ),
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
                    ],
                ),
            ),
            # Fourth datum uses a consumer identity matching our QR bag, and contains
            # one item, which has no barcode.
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
                            product_code=None,
                            count=self.product_count_1,
                        ),
                    ],
                ),
            ),
        ]

        with patch(self._mock_api_path, return_value=self._get_mock_api(data)):
            # Act: run command twice on same input to ensure idempotency
            buf = StringIO()
            call_command(Command(), stdout=buf, stderr=buf)
            call_command(Command(), stdout=buf, stderr=buf)

            # Assert: check the output
            self.assertIn("Importing ...", buf.getvalue())
            self.assertIn("Not importing anything", buf.getvalue())

            # Assert: check the `DepositPayout`/`DepositPayoutItem` objects
            self._assert_objects_created()

            # Assert: check the `QRBag` object was updated as expected
            self.qr_bag.refresh_from_db()
            self.assertEqual(self.qr_bag.status, "esani_optalt")

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
        expected_item_count = 5  # 2 + 1 + 1 + 1 = 5 objects
        self.assertQuerySetEqual(
            DepositPayout.objects.all(),
            [(DepositPayout.SOURCE_TYPE_API, "url", expected_item_count)],
            transform=lambda obj: (
                obj.source_type,
                obj.source_identifier,
                obj.item_count,
            ),
            ordered=False,
        )
        # Assert we create exactly three `DepositPayoutItems` (even though we run the
        # same import twice.) Check that the fields are set as expected.
        self.assertQuerySetEqual(
            DepositPayoutItem.objects.all(),
            [
                # First datum produces two objects
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
                # Second datum produces one object
                (
                    None,  # kiosk cvr
                    None,  # product
                    "product_code",  # unknown product barcode
                    0,  # product count
                    self.rvm_serial_number,
                    date(2020, 1, 1),
                    self.consumer_session_id,
                    "unknown_bag_qr",  # unknown QR code
                ),
                # Third datum produces one object
                (
                    self.kiosk_cvr,
                    self.product_1,
                    self.product_barcode_1,
                    self.product_count_1,
                    self.rvm_serial_number,
                    date(2020, 1, 1),
                    self.consumer_session_id,
                    self.consumer_identity_ext_id,
                ),
                # Fourth datum produces one object
                (
                    self.kiosk_cvr,
                    None,  # product
                    None,  # barcode
                    self.product_count_1,
                    self.rvm_serial_number,
                    date(2020, 1, 1),
                    self.consumer_session_id,
                    self.bag_qr,
                ),
            ],
            transform=lambda obj: (
                obj.kiosk.cvr if obj.kiosk else None,
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

    def test_get_consumer_identity_returns_none_on_absent_identity(self):
        # Arrange
        cmd = Command()
        # Act and assert
        self.assertIsNone(cmd._get_consumer_identity(ConsumerSession()))

    def test_get_source_returns_none_on_absent_identity(self):
        # Arrange
        cmd = Command()
        # Act and assert
        self.assertIsNone(cmd._get_source(ConsumerSession(), Kiosk))

    @parametrize(
        "lookup,db_value,expected",
        [
            # 9-digit QR code input
            (
                EXAMPLE_QR_ID,
                f"1{EXAMPLE_QR_ID}deadbeef",
                True,
            ),
            # 10-digit QR code
            (
                f"1{EXAMPLE_QR_ID}",
                f"1{EXAMPLE_QR_ID}deadbeef",
                True,
            ),
            # 18-digit QR code
            (
                f"1{EXAMPLE_QR_ID}deadbeef",
                f"1{EXAMPLE_QR_ID}deadbeef",
                True,
            ),
            # QR code of unrecognized length
            (
                "1",
                f"1{EXAMPLE_QR_ID}deadbeef",
                False,
            ),
            # QR code of recognized length, but does not exist in DB
            (
                f"1{EXAMPLE_QR_ID}deadbeef",
                "",
                False,
            ),
        ],
    )
    def test_get_from_qr(self, lookup, db_value, expected):
        # Arrange
        QRBag.objects.update_or_create(qr=db_value, kiosk=self.kiosk)
        cmd = Command()
        # Act
        result = cmd._get_from_qr(lookup, Kiosk)
        # Assert
        if expected:
            self.assertEqual(result, self.kiosk)
        else:
            self.assertIsNone(result)

    def test_get_from_qr_raises_on_invalid_source_type(self):
        # Arrange
        QRBag.objects.update_or_create(
            qr=f"1{EXAMPLE_QR_ID}deadbeef",
            kiosk=self.kiosk,
        )
        cmd = Command()
        # Assert
        with self.assertRaises(ValueError):
            # Act
            cmd._get_from_qr(EXAMPLE_QR_ID, Company)

    def test_get_direct_company_branch(self):
        # Arrange
        cmd = Command()
        # Act
        result = cmd._get_direct(f"80002{self.company_branch.id:05}", CompanyBranch)
        # Assert
        self.assertEqual(result, self.company_branch)

    def test_get_direct_kiosk(self):
        # Arrange
        cmd = Command()
        # Act
        result = cmd._get_direct(f"90003{self.kiosk.id:05}", Kiosk)
        # Assert
        self.assertEqual(result, self.kiosk)

    def test_get_direct_returns_none_on_no_match(self):
        # Arrange
        cmd = Command()
        # Act
        result = cmd._get_direct("9000299999", CompanyBranch)
        # Assert
        self.assertIsNone(result)

    def test_get_direct_returns_none_on_unexpected_source_type(self):
        # Arrange
        cmd = Command()
        # Act
        result = cmd._get_direct(f"90002{self.company_branch.id:05}", Company)
        # Assert
        self.assertIsNone(result)

    def test_get_qr_bag_always_returns_none(self):
        # Arrange
        cmd = Command()
        # Act
        result = cmd._get_qr_bag(self.bag_qr, Kiosk)
        # Assert
        self.assertIsNone(result)

    @parametrize(
        "val,db_value,expected_result",
        [
            (None, None, date.today() - timedelta(days=30)),
            (None, date(2019, 1, 1), date(2019, 1, 1)),
            ("2020-01-31", None, date(2020, 1, 31)),
        ],
    )
    def test_get_previous_to_date(self, val, db_value, expected_result):
        # Arrange
        if db_value is not None:
            DepositPayout.objects.create(
                source_type=DepositPayout.SOURCE_TYPE_API,
                source_identifier="testing",
                from_date=db_value,
                to_date=db_value,
                item_count=0,
            )
        cmd = Command()
        # Act
        actual_result = cmd._get_previous_to_date(val)
        # Assert
        self.assertEqual(actual_result, expected_result)

    @parametrize(
        "val,expected_result",
        [
            (None, date.today()),
            ("2020-01-31", date(2020, 1, 31)),
        ],
    )
    def test_get_todays_to_date(self, val, expected_result):
        # Arrange
        cmd = Command()
        # Act
        actual_result = cmd._get_todays_to_date(val)
        # Assert
        self.assertEqual(actual_result, expected_result)
