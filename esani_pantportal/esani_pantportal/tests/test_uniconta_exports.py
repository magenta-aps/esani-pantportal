# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import uuid
from csv import DictReader
from datetime import date
from io import StringIO
from operator import itemgetter

from django.conf import settings
from django.test import TestCase, override_settings
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.exports.uniconta.exports import CreditNoteExport, DebtorExport
from esani_pantportal.models import (
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    QRBag,
    ReverseVendingMachine,
)
from esani_pantportal.tests.conftest import LoginMixin

CUSTOMER_1_NAME = "branch name"
CUSTOMER_1_CVR = 1111
CUSTOMER_1_LOCATION_ID = "2222"
CUSTOMER_2_NAME = "kiosk name"
CUSTOMER_2_CVR = 3333
CUSTOMER_2_LOCATION_ID = "4444"


class _SharedBase(ParametrizedTestCase, LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company = Company.objects.create(
            name="company name",
            city=cls._test_city,
            cvr=CUSTOMER_1_CVR,
        )
        cls.company_branch = CompanyBranch.objects.create(
            company=cls.company,
            name=CUSTOMER_1_NAME,
            city=cls._test_city,
            location_id=CUSTOMER_1_LOCATION_ID,
            qr_compensation=30,
        )
        cls.kiosk = Kiosk.objects.create(
            name=CUSTOMER_2_NAME,
            city=cls._test_city,
            cvr=CUSTOMER_2_CVR,
            location_id=CUSTOMER_2_LOCATION_ID,
        )

    def _get_csv_rows(self, stream):
        stream.seek(0)
        return list(DictReader(stream, delimiter=";"))


def _line_vals():
    return {
        "customer_invoice_account_id": None,
        "customer_name": CUSTOMER_1_NAME,
        "customer_cvr": CUSTOMER_1_CVR,
        "customer_location_id": CUSTOMER_1_LOCATION_ID,
        "from_date": "2020-01-01",
        "to_date": "2020-02-01",
        "already_exported": "n",
    }


@override_settings(DEFAULT_REFUND_VALUE=250)
class TestCreditNoteExport(_SharedBase):
    maxDiff = None

    qr_code = "1234"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company_branch_rvm = ReverseVendingMachine.objects.create(
            company_branch=cls.company_branch,
            compensation=15.0,
        )
        cls.kiosk_rvm = ReverseVendingMachine.objects.create(
            kiosk=cls.kiosk,
            compensation=25.0,
        )
        cls.qr_bag = QRBag.objects.create(
            company_branch=cls.company_branch,
            qr=cls.qr_code,
            status="esani_optalt",
        )
        cls.product = Product.objects.create(
            product_name="product",
            barcode="0010",
            refund_value=250,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.deposit_payout_rvm = cls._add_deposit_payout(DepositPayout.SOURCE_TYPE_CSV)
        cls.deposit_payout_bag = cls._add_deposit_payout(DepositPayout.SOURCE_TYPE_API)
        cls.deposit_payout_manual = cls._add_deposit_payout(
            DepositPayout.SOURCE_TYPE_MANUAL
        )
        cls.deposit_payout_item_rvm_1 = cls._add_deposit_payout_item(
            cls.deposit_payout_rvm,
            company_branch=cls.company_branch,
            barcode="barcode",
            product=cls.product,
        )
        cls.deposit_payout_item_rvm_2 = cls._add_deposit_payout_item(
            cls.deposit_payout_rvm,
            kiosk=cls.kiosk,
            barcode="barcode",
            product=cls.product,
        )
        cls.deposit_payout_item_bag_1 = cls._add_deposit_payout_item(
            cls.deposit_payout_bag,
            company_branch=cls.company_branch,
            barcode="barcode",
            qr_bag=cls.qr_bag,
            product=cls.product,
            count=50,
        )
        cls.deposit_payout_item_with_file_id = cls._add_deposit_payout_item(
            cls.deposit_payout_bag,
            company_branch=cls.company_branch,
            barcode="barcode",
            product=cls.product,
            file_id=uuid.uuid4(),
        )
        # Bag item without product FK - must be exported with default refund amount
        cls.deposit_payout_item_null_product = cls._add_deposit_payout_item(
            cls.deposit_payout_bag,
            company_branch=cls.company_branch,
            barcode="barcode",
            product=None,
            count=100,
        )
        # Bag item without source (company branch or kiosk) - must *never* be
        # exported.
        cls.deposit_payout_item_null_source = cls._add_deposit_payout_item(
            cls.deposit_payout_bag,
            company_branch=None,
            kiosk=None,
            barcode="barcode",
            product=cls.product,
            count=9000,
        )
        # Manually created item - must be exported
        cls.deposit_payout_item_manual = cls._add_deposit_payout_item(
            cls.deposit_payout_manual,
            kiosk=cls.kiosk,
            barcode=None,
            product=cls.product,
            location_id=None,
            count=1000,
            compensation=333,
        )
        # "Null" item (#59706) from Tomra API - must not be exported
        cls.deposit_payout_item_null_barcode = cls._add_deposit_payout_item(
            cls.deposit_payout_bag,
            kiosk=cls.kiosk,
            barcode=None,
            product=cls.product,
            location_id=cls.kiosk.location_id,
            count=1,
        )

    @classmethod
    def _add_deposit_payout(cls, source_type):
        return DepositPayout.objects.create(
            source_type=source_type,
            source_identifier="unused",
            from_date=date(2020, 1, 1),
            to_date=date(2020, 1, 2),
            item_count=0,
        )

    @classmethod
    def _add_deposit_payout_item(cls, deposit_payout, **kwargs):
        kwargs.setdefault("count", 20)
        return DepositPayoutItem.objects.create(
            deposit_payout=deposit_payout,
            date=date(2020, 1, 1),
            **kwargs,
        )

    def _get_instance(self, **kwargs):
        return CreditNoteExport(
            date(2020, 1, 1),
            date(2020, 2, 1),
            DepositPayoutItem.objects.all(),
            **kwargs,
        )

    def setUp(self):
        super().setUp()
        self.instance = self._get_instance()

    def test_init_raises_on_dry_true_and_file_id_given(self):
        """Raise ValueError if a `file_id` is passed, and `dry=False`"""
        with self.assertRaises(ValueError):
            self._get_instance(dry=False, file_id=uuid.uuid4())

    def test_iter(self):
        # Act (consume iterable)
        items = list(self.instance)
        # Assert that iterable contains (at least) four items.
        # Two from `cls.deposit_payout_item_rvm_1` and two from
        # `cls.deposit_payout_item_rvm_1`.
        self.assertGreaterEqual(len(items), 4)

    @parametrize(
        "dry,expected_keys,expected_list",
        [
            (
                True,
                ["already_exported"],
                [
                    # From `cls.deposit_payout_item_rvm_1`
                    ("101", "250", "20"),
                    ("201", "15", "20"),
                    # From `cls.deposit_payout_item_bag_1` (count=50)
                    # and `cls.deposit_payout_item_null_product` (count=100)
                    ("102", "250", "150"),
                    ("202", "30", "150"),
                    # From `cls.deposit_payout_item_file_id`
                    ("102", "250", "20"),
                    ("202", "30", "20"),
                    # From `cls.deposit_payout_item_rvm_2`
                    ("101", "250", "20"),
                    ("201", "15", "20"),
                    # From `self.deposit_payout_item_manual` (count=1000)
                    ("103", "250", "1000"),
                    ("203", "333", "1000"),
                ],
            ),
            (
                False,
                ["file_id"],
                [
                    # From `cls.deposit_payout_item_rvm_1`
                    ("101", "250", "20"),
                    ("201", "15", "20"),
                    # From `cls.deposit_payout_item_bag_1` (count=50)
                    # and `cls.deposit_payout_item_null_product` (count=100)
                    ("102", "250", "150"),
                    ("202", "30", "150"),
                    # From `cls.deposit_payout_item_rvm_2`
                    ("101", "250", "20"),
                    ("201", "15", "20"),
                    # From `self.deposit_payout_item_manual` (count=1000)
                    ("103", "250", "1000"),
                    ("203", "333", "1000"),
                ],
            ),
        ],
    )
    def test_as_csv(self, dry, expected_keys, expected_list):
        # Arrange
        instance = self._get_instance(dry=dry)
        stream = StringIO()
        # Act
        instance.as_csv(stream)
        # Assert that we got the expected lines by looking at the product IDs
        actual_list = [
            (row["product_id"], row["unit_price"], row["quantity"])
            for row in self._get_csv_rows(stream)
        ]

        self.assertListEqual(actual_list, expected_list)
        # Assert that all lines have the expected fields
        expected_keys = set(self.instance._field_names + expected_keys)
        self.assertTrue(
            all(
                (set(row.keys()) == expected_keys) for row in self._get_csv_rows(stream)
            )
        )

    def test_get_filename(self):
        # Act
        filename = self.instance.get_filename()
        # Assert
        self.assertRegex(filename, r"kreditnota_2020\-01\-01_2020\-02\-01_(.*?)\.csv")

    @parametrize(
        "dry,expected",
        [
            (
                # Dry?
                True,
                # Expected result
                [
                    {
                        "already_exported": False,
                        "bag_qrs": [None],
                        "count": 20,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "company_branch",
                        "type": "csv",
                    },
                    # This line combines the data from
                    # `self.deposit_payout_item_bag_1` (count=50) and
                    # `self.deposit_payout_item_null_product` (count=100)
                    {
                        "already_exported": False,
                        "bag_qrs": [None],
                        "count": 50 + 100,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "company_branch",
                        "type": "api",
                    },
                    {
                        "already_exported": True,
                        "bag_qrs": [None],
                        "count": 20,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "company_branch",
                        "type": "api",
                    },
                    {
                        "already_exported": False,
                        "bag_qrs": [None],
                        "count": 20,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "kiosk",
                        "type": "csv",
                    },
                    # Data from `self.deposit_payout_item_manual`
                    {
                        "already_exported": False,
                        "bag_qrs": [None],
                        "count": 1000,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": 333,
                        "source": "kiosk",
                        "type": "manual",
                    },
                ],
            ),
            (
                # Dry?
                False,
                # Expected result
                [
                    {
                        "bag_qrs": [None],
                        "count": 20,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "company_branch",
                        "type": "csv",
                    },
                    # This line combines the data from
                    # `self.deposit_payout_item_bag_1` (count=50) and
                    # `self.deposit_payout_item_null_product` (count=100)
                    {
                        "bag_qrs": [None],
                        "count": 50 + 100,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "company_branch",
                        "type": "api",
                    },
                    {
                        "bag_qrs": [None],
                        "count": 20,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": None,
                        "source": "kiosk",
                        "type": "csv",
                    },
                    # Data from `self.deposit_payout_item_manual`
                    {
                        "bag_qrs": [None],
                        "count": 1000,
                        "product_refund_value": 250,
                        "rvm_refund_value": None,
                        "compensation": 333,
                        "source": "kiosk",
                        "type": "manual",
                    },
                ],
            ),
        ],
    )
    def test_get_base_queryset(self, dry, expected):
        # Arrange
        instance = self._get_instance(dry=dry)
        # Act
        actual = instance._get_base_queryset(DepositPayoutItem.objects.all())
        # Assert
        self.assertQuerySetEqual(
            # Drop `source_id` from actual result items, as we cannot reliably test
            # against it (it is a database ID which may change.)
            [
                {key: value for key, value in val.items() if key != "source_id"}
                for val in actual
            ],
            expected,
        )

    @parametrize(
        "row,expected_lines",
        [
            # Test 1
            (
                # Input row: 1000 items from CSV (clearing reports)
                {
                    "_source_name": CUSTOMER_1_NAME,
                    "type": DepositPayout.SOURCE_TYPE_CSV,
                    "source": "company_branch",
                    "product_refund_value": 200,
                    "rvm_refund_value": 15,
                    "count": 1000,
                    "bag_qrs": [],
                    "compensation": None,
                    "already_exported": False,
                },
                [
                    # First line is "Pant (automat)"
                    {
                        "product_id": 101,
                        "product_name": "Pant (automat)",
                        "quantity": 1000,
                        "unit_price": 200,
                        "total": 1000 * 200,
                        **_line_vals(),
                    },
                    # Second line is "Håndteringsgodtgørelse (automat)"
                    {
                        "product_id": 201,
                        "product_name": "Håndteringsgodtgørelse (automat)",
                        "quantity": 1000,
                        "unit_price": 15,
                        "total": 1000 * 15,
                        **_line_vals(),
                    },
                ],
            ),
            # Test 2
            (
                # Input row: 1000 items from API (consumer sessions.)
                # This input row also contains `bag_qrs`.
                {
                    "_source_name": CUSTOMER_1_NAME,
                    "type": DepositPayout.SOURCE_TYPE_API,
                    "source": "company_branch",
                    "product_refund_value": 200,
                    "rvm_refund_value": 15,
                    "count": 1000,
                    "compensation": None,
                    # One bag QR starting with 0 (known prefix), Two bag QRs starting
                    # with 1 (known prefix), and one bag QR starting with 2 (unknown
                    # prefix.)
                    "bag_qrs": ["001", "100", "101", "200"],
                    "already_exported": False,
                },
                [
                    # First line is "Pant (pose)"
                    {
                        "product_id": 102,
                        "product_name": "Pant (pose)",
                        "quantity": 1000,
                        "unit_price": 200,
                        "total": 1000 * 200,
                        **_line_vals(),
                    },
                    # Second line is "Håndteringsgodtgørelse (pose)"
                    {
                        "product_id": 202,
                        "product_name": "Håndteringsgodtgørelse (pose)",
                        "quantity": 1000,
                        "unit_price": 30,
                        "total": 1000 * 30,
                        **_line_vals(),
                    },
                    # Third line is "Lille pose"
                    {
                        "product_id": 901,
                        "product_name": "Lille pose",
                        "quantity": 1,  # Corresponds to the one bag QR starting with 0
                        "unit_price": -275,
                        "total": 1 * -275,
                        **_line_vals(),
                    },
                    # Fourth line is "Stor pose"
                    {
                        "product_id": 902,
                        "product_name": "Stor pose",
                        "quantity": 2,  # Corresponds to the two bag QRs starting with 1
                        "unit_price": -525,
                        "total": 2 * -525,
                        **_line_vals(),
                    },
                ],
            ),
        ],
    )
    def test_get_lines_for_row_dry(self, row, expected_lines):
        # Arrange: get "dry" instance
        instance = self._get_instance(dry=True)

        # Arrange: add `source_id` to `row` at runtime (to avoid hardcoding object IDs)
        customer = CompanyBranch.objects.get(name=row["_source_name"])
        row["source_id"] = customer.id
        del row["_source_name"]

        # Arrange: add `customer_id` to all `expected_lines`
        for line in expected_lines:
            line["customer_id"] = customer.external_customer_id

        # Act
        actual_lines = instance._get_lines_for_row(row)

        # Assert
        self.assertListEqual(list(actual_lines), expected_lines)

    def test_get_lines_for_row_wet(self):
        # Arrange: get "wet" instance
        instance = self._get_instance(dry=False)

        # Arrange: construct `row` input
        customer = CompanyBranch.objects.get(name=CUSTOMER_1_NAME)
        row = {
            "source_id": customer.id,
            "customer_id": customer.external_customer_id,
            "type": DepositPayout.SOURCE_TYPE_CSV,
            "source": "company_branch",
            "product_refund_value": 200,
            "rvm_refund_value": 15,
            "count": 1000,
            "compensation": None,
            "bag_qrs": [],
            "file_id": None,
        }

        # Act
        actual_lines = instance._get_lines_for_row(row)

        # Assert: all lines contain `file_id`
        self.assertIsNotNone(instance._file_id)
        self.assertTrue(
            all([line["file_id"] == instance._file_id for line in actual_lines])
        )

    @parametrize(
        "bag_qrs,expected_groups",
        [
            ([], []),
            (None, []),
            (
                # List consists of empty QR, plus QR of unknown prefix
                [None, "57"],
                # No bag groups
                [],
            ),
            (
                # Empty QR, plus 2 unique QRs sharing same prefix ("1")
                [None, "1001", "1001", "1002"],
                # Count 2 bags with prefix = 1
                [("1", 2)],
            ),
        ],
    )
    def test_get_bag_groups_handles_empty_or_absent_values(
        self, bag_qrs, expected_groups
    ):
        # Arrange
        row = {"bag_qrs": bag_qrs}
        # Act
        groups = self.instance._get_bag_groups(row)
        # Assert
        self.assertListEqual(groups, expected_groups)

    def test_get_customer_returns_company_branch(self):
        # Arrange
        row = {"source": "company_branch", "source_id": self.company_branch.id}
        # Act
        customer = self.instance._get_customer(row)
        # Assert
        self.assertEqual(customer, self.company_branch)

    def test_get_customer_returns_kiosk(self):
        # Arrange
        row = {"source": "kiosk", "source_id": self.kiosk.id}
        # Act
        customer = self.instance._get_customer(row)
        # Assert
        self.assertEqual(customer, self.kiosk)

    @parametrize("dry", [(True,), (False,)])
    def test_get_file_id(self, dry):
        # Arrange
        instance = self._get_instance(dry=dry)
        # Act
        file_id = instance.get_file_id()
        # Assert
        if dry:
            self.assertIsNone(file_id)
        else:
            self.assertEqual(file_id, instance._file_id)

    def test_dry_false(self):
        """Passing `dry=False` should update the underlying objects"""
        # Arrange and act (consume iterable)
        instance = self._get_instance(dry=False)
        list(instance)

        # Assert: Deposit payout items are marked as exported
        self._assert_items_have_file_id(
            [
                self.deposit_payout_item_rvm_1,
                self.deposit_payout_item_rvm_2,
                self.deposit_payout_item_bag_1,
                self.deposit_payout_item_null_product,
                self.deposit_payout_item_manual,
            ],
            instance._file_id,
        )

        # Assert: "Other" deposit payout items are *not* marked as exported
        self._assert_items_have_no_file_id(
            [
                self.deposit_payout_item_null_source,
                self.deposit_payout_item_null_barcode,
            ]
        )

        # Assert: deposit payout items with a current file ID are *not*
        # marked as exported (with the new file ID.)
        self._assert_items_have_file_id(
            [self.deposit_payout_item_with_file_id],
            self.deposit_payout_item_with_file_id.file_id,
        )

        # Assert: QR bag status is updated
        self.qr_bag.refresh_from_db()
        self.assertEqual(self.qr_bag.status, "esani_udbetalt")

    def test_dry_true(self):
        """Passing `dry=True` should *not* update the underlying objects"""
        # Arrange and act (consume iterable)
        list(self._get_instance(dry=True))

        # Assert: Deposit payout items are *not* marked as exported
        self._assert_items_have_no_file_id(
            [
                self.deposit_payout_item_rvm_1,
                self.deposit_payout_item_rvm_2,
                self.deposit_payout_item_bag_1,
                self.deposit_payout_item_null_product,
                self.deposit_payout_item_manual,
                self.deposit_payout_item_null_source,
                self.deposit_payout_item_null_barcode,
            ]
        )

        # Assert: deposit payout items with a current file ID are *not*
        # marked as exported, and keep their current file ID.
        self._assert_items_have_file_id(
            [self.deposit_payout_item_with_file_id],
            self.deposit_payout_item_with_file_id.file_id,
        )

        # Assert: QR bag status is *not* updated
        self.qr_bag.refresh_from_db()
        self.assertEqual(self.qr_bag.status, "esani_optalt")

    def _assert_items_have_file_id(self, items, file_id):
        for item in items:
            with self.subTest(str(item)):
                item.refresh_from_db()
                self.assertEqual(item.file_id, file_id)

    def _assert_items_have_no_file_id(self, items):
        for item in items:
            with self.subTest(str(item)):
                item.refresh_from_db()
                self.assertIsNone(item.file_id)


class TestDebtorExport(_SharedBase):
    maxDiff = None

    def _get_expected_row_values(self):
        return [
            # `Company` row
            ("company name", CUSTOMER_1_CVR, None, f"1-{self.company.id:05}"),
            # `CompanyBranch` row
            (
                CUSTOMER_1_NAME,
                CUSTOMER_1_CVR,  # same as on `Company` row
                CUSTOMER_1_LOCATION_ID,
                f"2-{self.company_branch.id:05}",
            ),
            # `Kiosk` row
            (
                CUSTOMER_2_NAME,
                CUSTOMER_2_CVR,
                CUSTOMER_2_LOCATION_ID,
                f"3-{self.kiosk.id:05}",
            ),
        ]

    def _assert_expected_csv_rows(self, stream):
        def transform(row):
            return (
                row["name"],
                int(row["cvr"]) if row["cvr"] else None,
                str(row["location_id"]) if row["location_id"] else None,
                row["id"],
            )

        self.assertListEqual(
            self._get_expected_row_values(),
            [transform(row) for row in self._get_csv_rows(stream)],
        )

    def test_get_queryset(self):
        # Arrange
        instance = DebtorExport()
        # Act
        qs = instance._get_queryset()
        # Assert that the queryset contains three rows with the specific values given
        self.assertQuerySetEqual(
            qs,
            self._get_expected_row_values(),
            transform=itemgetter("name", "_cvr", "_location_id", "_id"),
        )
        # Assert that the columns of the queryset match the fields listed in `_common`,
        # plus `_cvr`, `_location_id` and `_id`.
        self.assertSetEqual(
            set(qs.query.values_select).union(set(qs.query.annotation_select.keys())),
            set(instance._common + ["_cvr", "_location_id", "_id"]),
        )

    def test_as_csv(self):
        # Arrange
        instance = DebtorExport()
        stream = StringIO()
        # Act
        instance.as_csv(stream=stream)
        # Assert
        self._assert_expected_csv_rows(stream)


class TestManuallyCreatedItemsExport(_SharedBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.manually_added_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_MANUAL,
            source_identifier="unused",
            from_date=date(2020, 1, 1),
            to_date=date(2020, 1, 1),
            item_count=1,
        )
        cls.manually_added_item = DepositPayoutItem.objects.create(
            deposit_payout=cls.manually_added_payout,
            date=date(2020, 1, 1),
            compensation=66,
            count=666,
            company_branch=cls.company_branch,
        )

    def test_export(self):
        instance = CreditNoteExport(
            date(2020, 1, 1),
            date(2020, 2, 1),
            DepositPayoutItem.objects.all(),
        )

        stream = StringIO()
        instance.as_csv(stream)

        output = [
            (row["product_id"], row["unit_price"]) for row in self._get_csv_rows(stream)
        ]
        output_dict = {k: v for k, v in output}

        self.assertEqual(len(output), 2)
        self.assertEqual(output_dict["103"], str(settings.DEFAULT_REFUND_VALUE))
        self.assertEqual(output_dict["203"], str(self.manually_added_item.compensation))
