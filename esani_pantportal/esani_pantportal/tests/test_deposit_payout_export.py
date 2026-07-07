# SPDX-FileCopyrightText: 2026 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import os
import shutil
import tempfile
import uuid
from datetime import date
from io import StringIO

import pandas as pd
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from esani_pantportal.models import (
    City,
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
)

# Column headers (must match the command's `HEADER`).
SOURCE = "Kæde, butik (eller RVM-serienummer)"
PRODUCT = "Produkt (eller stregkode)"
REFUND = "Pantværdi (i øre)"
COUNT = "Antal"
DATE = "Dato"
EXPORTED = "Allerede eksporteret"
BARCODE = "Stregkode/Ean"
CITY = "By"


class ExportDepositPayoutsToCSVTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Testby")

        cls.company = Company.objects.create(
            name="company name",
            cvr=1111,
            city=cls.city,
        )
        cls.company_branch = CompanyBranch.objects.create(
            company=cls.company,
            name="branch name",
            city=cls.city,
            location_id="2222",
        )
        cls.kiosk = Kiosk.objects.create(
            name="kiosk name",
            cvr=3333,
            city=cls.city,
            location_id="4444",
        )
        cls.product = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        cls.payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_MANUAL,
            source_identifier="unused",
            from_date=date(2020, 1, 1),
            to_date=date(2020, 1, 1),
            item_count=4,
        )

        # Item linked to a company branch and a product. `count` is unique per item
        # so we can use it to look up rows (the export is deliberately unordered).
        cls.item_branch = DepositPayoutItem.objects.create(
            deposit_payout=cls.payout,
            company_branch=cls.company_branch,
            product=cls.product,
            date=date(2020, 1, 1),
            count=666,
            barcode="0010",
        )
        # Item linked to a kiosk and a product.
        cls.item_kiosk = DepositPayoutItem.objects.create(
            deposit_payout=cls.payout,
            kiosk=cls.kiosk,
            product=cls.product,
            date=date(2021, 6, 15),
            count=10,
            barcode="0011",
        )
        # Item with neither branch/kiosk nor product, only an RVM serial number.
        cls.item_rvm = DepositPayoutItem.objects.create(
            deposit_payout=cls.payout,
            rvm_serial="99999",
            date=date(2022, 3, 3),
            count=5,
            barcode="0002",
        )
        # Item that has already been exported (`file_id` is set).
        cls.item_exported = DepositPayoutItem.objects.create(
            deposit_payout=cls.payout,
            company_branch=cls.company_branch,
            product=cls.product,
            date=date(2020, 5, 5),
            count=1,
            barcode="0010",
            file_id=uuid.uuid4(),
        )

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def run_export(self, filename="export.csv", **options):
        out = StringIO()
        call_command(
            "export_deposit_payouts_to_csv",
            self.tmpdir,
            filename=filename,
            stdout=out,
            **options,
        )
        return os.path.join(self.tmpdir, filename), out.getvalue()

    def read_export(self, **options):
        path, _ = self.run_export(**options)
        # `keep_default_na=False` keeps empty cells as "" instead of NaN. The
        # barcode/refund/exported columns are read as strings to keep leading
        # zeros and avoid dtype guesswork.
        df = pd.read_csv(
            path,
            sep=";",
            encoding="utf-8-sig",
            keep_default_na=False,
            dtype={BARCODE: str, REFUND: str, EXPORTED: str},
        )
        return df

    def test_exports_all_rows_by_default(self):
        df = self.read_export()
        self.assertEqual(len(df), 4)

    def test_company_branch_row_contents(self):
        df = self.read_export().set_index(COUNT)
        row = df.loc[666]
        # `source` uses the company name, not the branch name.
        self.assertEqual(row[SOURCE], "company name")
        self.assertEqual(row[PRODUCT], "prod1")
        self.assertEqual(row[REFUND], "3")
        self.assertEqual(row[DATE], "2020-01-01")
        self.assertEqual(row[EXPORTED], "False")
        self.assertEqual(row[BARCODE], "0010")
        self.assertEqual(row[CITY], "Testby")

    def test_kiosk_row_contents(self):
        df = self.read_export().set_index(COUNT)
        row = df.loc[10]
        self.assertEqual(row[SOURCE], "kiosk name")
        self.assertEqual(row[CITY], "Testby")

    def test_rvm_only_row_contents(self):
        df = self.read_export().set_index(COUNT)
        row = df.loc[5]
        # No branch/kiosk: falls back to the RVM serial number.
        self.assertEqual(row[SOURCE], "99999")
        # No product: empty product name and a placeholder refund value.
        self.assertEqual(row[PRODUCT], "")
        self.assertEqual(row[REFUND], "-")
        # No branch/kiosk: placeholder city.
        self.assertEqual(row[CITY], "-")

    def test_already_exported_flag(self):
        df = self.read_export().set_index(COUNT)
        self.assertEqual(df.loc[1, EXPORTED], "True")
        self.assertEqual(df.loc[666, EXPORTED], "False")

    def test_from_date_filter(self):
        df = self.read_export(from_date=date(2021, 1, 1)).set_index(COUNT)
        # Excludes the two items from 2020.
        self.assertEqual(sorted(df.index), [5, 10])

    def test_to_date_filter(self):
        df = self.read_export(to_date=date(2020, 12, 31)).set_index(COUNT)
        # Only the two items from 2020.
        self.assertEqual(sorted(df.index), [1, 666])

    def test_company_branch_filter(self):
        df = self.read_export(company_branch=self.company_branch.id).set_index(COUNT)
        self.assertEqual(sorted(df.index), [1, 666])

    def test_kiosk_filter(self):
        df = self.read_export(kiosk=self.kiosk.id).set_index(COUNT)
        self.assertEqual(sorted(df.index), [10])

    def test_not_exported_only(self):
        df = self.read_export(not_exported_only=True).set_index(COUNT)
        # Excludes the already-exported item (count=1).
        self.assertEqual(sorted(df.index), [5, 10, 666])

    def test_custom_delimiter(self):
        path, _ = self.run_export(delimiter=",")
        df = pd.read_csv(path, sep=",", encoding="utf-8-sig", keep_default_na=False)
        self.assertEqual(len(df), 4)

    def test_empty_result(self):
        _, stdout = self.run_export(from_date=date(2030, 1, 1))
        self.assertIn("Wrote 0 rows", stdout)
        df = self.read_export(from_date=date(2030, 1, 1))
        self.assertEqual(len(df), 0)

    def test_invalid_date_raises(self):
        # Pass the option as a string arg so argparse applies the `type=` parser
        # (`_parse_date`), which is what raises for a malformed date.
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "export_deposit_payouts_to_csv",
                self.tmpdir,
                "--from-date",
                "not-a-date",
                stdout=out,
            )

    def test_invalid_path_raises(self):
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "export_deposit_payouts_to_csv",
                os.path.join(self.tmpdir, "does-not-exist"),
                stdout=out,
            )
