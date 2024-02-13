# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from csv import DictReader
from datetime import date
from io import StringIO
from operator import itemgetter

from django.test import TestCase
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.exports.uniconta.exports import CreditNoteExport, DebtorExport
from esani_pantportal.models import (
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    ReverseVendingMachine,
)

CUSTOMER_1_NAME = "branch name"
CUSTOMER_1_CVR = 1111
CUSTOMER_1_LOCATION_ID = 2222
CUSTOMER_2_NAME = "kiosk name"
CUSTOMER_2_CVR = 3333
CUSTOMER_2_LOCATION_ID = 4444


class _SharedBase(ParametrizedTestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company = Company.objects.create(
            name="company name",
            cvr=CUSTOMER_1_CVR,
        )
        cls.company_branch = CompanyBranch.objects.create(
            company=cls.company,
            name=CUSTOMER_1_NAME,
            location_id=CUSTOMER_1_LOCATION_ID,
            qr_compensation=30,
        )
        cls.kiosk = Kiosk.objects.create(
            name=CUSTOMER_2_NAME,
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
    }


class TestCreditNoteExport(_SharedBase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company_branch_rvm = ReverseVendingMachine.objects.create(
            company_branch=cls.company_branch,
            compensation=15,
        )
        cls.kiosk_rvm = ReverseVendingMachine.objects.create(
            kiosk=cls.kiosk,
            compensation=25,
        )
        cls.product = Product.objects.create(
            product_name="product",
            barcode="0010",
            refund_value=250,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.deposit_payout_rvm = cls._add_deposit_payout(DepositPayout.SOURCE_TYPE_CSV)
        cls.deposit_payout_bag = cls._add_deposit_payout(DepositPayout.SOURCE_TYPE_API)
        cls.deposit_payout_item_rvm_1 = cls._add_deposit_payout_item(
            cls.deposit_payout_rvm,
            company_branch=cls.company_branch,
        )
        cls.deposit_payout_item_rvm_2 = cls._add_deposit_payout_item(
            cls.deposit_payout_rvm,
            kiosk=cls.kiosk,
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
        return DepositPayoutItem.objects.create(
            deposit_payout=deposit_payout,
            product=cls.product,
            rvm_serial=0,
            location_id=0,
            barcode="",
            date=date(2020, 1, 1),
            count=20,
            **kwargs,
        )

    def setUp(self):
        self.instance = CreditNoteExport(
            date(2020, 1, 1),
            date(2020, 2, 1),
            DepositPayoutItem.objects.all(),
        )

    def test_iter(self):
        # Act (consume iterable)
        items = list(self.instance)
        # Assert that iterable contains (at least) four items.
        # Two from `cls.deposit_payout_item_rvm_1` and two from
        # `cls.deposit_payout_item_rvm_1`.
        self.assertGreaterEqual(len(items), 4)

    def test_as_csv(self):
        # Arrange
        stream = StringIO()
        # Act
        self.instance.as_csv(stream)
        # Assert that we got the expected lines by looking at the product IDs
        self.assertListEqual(
            [row["product_id"] for row in self._get_csv_rows(stream)],
            [
                # From `cls.deposit_payout_item_rvm_1`
                "101",
                "201",
                # From `cls.deposit_payout_item_rvm_2`
                "101",
                "201",
            ],
        )
        # Assert that all lines have the expected fields
        self.assertTrue(
            all(
                (set(row.keys()) == set(self.instance._field_names))
                for row in self._get_csv_rows(stream)
            )
        )

    def test_get_filename(self):
        # Act
        filename = self.instance.get_filename()
        # Assert
        self.assertRegex(filename, r"kreditnota_2020\-01\-01_2020\-02\-01_(.*?)\.csv")

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
                    # One bag QR starting with 0 (known prefix), Two bag QRs starting
                    # with 1 (known prefix), and one bag QR starting with 2 (unknown
                    # prefix.)
                    "bag_qrs": ["001", "100", "101", "200"],
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
    def test_get_lines_for_row(self, row, expected_lines):
        def filter_items(lines, remove=("file_id",)):
            for line in lines:
                for key in remove:
                    del line[key]
                yield line

        # Arrange: add `source_id` to `row` at runtime (to avoid hardcoding object IDs)
        customer = CompanyBranch.objects.get(name=row["_source_name"])
        row["source_id"] = customer.id
        del row["_source_name"]
        # Arrange: add `customer_id` to all `expected_lines`
        for line in expected_lines:
            line["customer_id"] = customer.external_customer_id

        # Act
        actual_lines = self.instance._get_lines_for_row(row)
        # Assert
        self.assertListEqual(list(filter_items(actual_lines)), expected_lines)

    @parametrize("bag_qrs", [([],), (None,)])
    def test_get_bag_groups_handles_empty_or_absent_list(self, bag_qrs):
        # Arrange
        row = {"bag_qrs": bag_qrs}
        # Act
        groups = self.instance._get_bag_groups(row)
        # Assert
        self.assertListEqual(groups, [])

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
                int(row["location_id"]) if row["location_id"] else None,
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
