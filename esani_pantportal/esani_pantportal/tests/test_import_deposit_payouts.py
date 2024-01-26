# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import datetime
from io import StringIO
from unittest.mock import ANY, MagicMock, mock_open, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from esani_pantportal.management.commands.import_deposit_payouts import (
    SFTP,
    Command,
    LocalFilesystem,
    Source,
)
from esani_pantportal.models import (
    DepositPayout,
    DepositPayoutItem,
    Kiosk,
    Product,
    RefundMethod,
)


class TestImportDepositPayouts(TestCase):
    maxDiff = None

    kiosk_cvr = 1234

    refund_method_1_serial_number = "3"
    refund_method_2_serial_number = "4"

    product_barcode_1 = "839728179970"
    product_barcode_2 = "3662195622914"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Add `Kiosk` object
        kiosk = Kiosk.objects.create(cvr=cls.kiosk_cvr)

        # Add `RefundMethod` objects matching the RVM serial numbers in
        # `example_with_valid_ids.csv`.
        RefundMethod.objects.update_or_create(
            kiosk=kiosk,
            serial_number=cls.refund_method_1_serial_number,
        )
        RefundMethod.objects.update_or_create(
            kiosk=kiosk,
            serial_number=cls.refund_method_2_serial_number,
        )

        # Add `Product` objects matching the barcodes in `example_with_valid_ids.csv`
        defaults = {
            "height": 250,
            "diameter": 50,
            "weight": 20,
            "capacity": 330,
            "shape": "F",
        }
        Product.objects.update_or_create(
            product_name="Foo",
            barcode=cls.product_barcode_1,
            defaults=defaults,
        )
        Product.objects.update_or_create(
            product_name="Bar",
            barcode=cls.product_barcode_2,
            defaults=defaults,
        )

    def test_import_creates_expected_objects(self):
        def item(**kwargs):
            default = {
                "deposit_payout__from_date": datetime.date(2023, 10, 23),
                "deposit_payout__to_date": datetime.date(2023, 10, 23),
                "date": datetime.date(2023, 10, 23),
            }
            default.update(**kwargs)
            return default

        # Arrange
        buf = StringIO()

        # Act
        call_command(Command(), stdout=buf, stderr=buf)

        # Assert: fetch the `DepositPayoutItem` objects created by `Command`
        fields = [
            "deposit_payout__source_identifier",
            "deposit_payout__from_date",
            "deposit_payout__to_date",
            "company_branch__company__cvr",
            "kiosk__cvr",
            "product__barcode",
            "location_id",
            "rvm_serial",
            "date",
            "barcode",
            "count",
        ]
        actual_items = DepositPayoutItem.objects.all().values(*fields).order_by(*fields)
        # Assert: define list of expected `DepositPayoutItem` objects
        expected_items = [
            # Lines from `example_original.csv` are not related to `CompanyBranch`,
            # `Kiosk` or `Product` objects, as their IDs (`rvm_serial` and `barcode`)
            # do not match any `CompanyBranch`, `Kiosk` or `Product` objects in the
            # database.
            item(
                deposit_payout__source_identifier="example_original.csv",
                date=datetime.date(2023, 10, 21),
                company_branch__company__cvr=None,
                kiosk__cvr=None,
                product__barcode=None,
                location_id=126161,
                rvm_serial=936860206,
                barcode="5000112630251",
                count=20,
            ),
            item(
                deposit_payout__source_identifier="example_original.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=None,
                product__barcode=None,
                location_id=126161,
                rvm_serial=936860206,
                barcode="5000112630251",
                count=500,
            ),
            item(
                deposit_payout__source_identifier="example_original.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=None,
                product__barcode=None,
                location_id=126161,
                rvm_serial=936860207,
                barcode="3179732368911",
                count=2,
            ),
            item(
                deposit_payout__source_identifier="example_original.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=None,
                product__barcode=None,
                location_id=126161,
                rvm_serial=936860207,
                barcode="3179732368911",
                count=200,
            ),
            # Lines from `example_with_valid_ids.csv` *are* related to `Kiosk` and
            # `Product` objects, as their IDs (`rvm_serial` and `barcode`)
            # match `Kiosk` and `Product` objects in the database.
            item(
                deposit_payout__source_identifier="example_with_valid_ids.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=self.kiosk_cvr,
                product__barcode=self.product_barcode_2,
                location_id=2,
                rvm_serial=int(self.refund_method_2_serial_number),
                barcode=self.product_barcode_2,
                count=2,
            ),
            item(
                deposit_payout__source_identifier="example_with_valid_ids.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=self.kiosk_cvr,
                product__barcode=self.product_barcode_2,
                location_id=2,
                rvm_serial=int(self.refund_method_2_serial_number),
                barcode=self.product_barcode_2,
                count=200,
            ),
            item(
                deposit_payout__source_identifier="example_with_valid_ids.csv",
                date=datetime.date(2023, 10, 21),
                company_branch__company__cvr=None,
                kiosk__cvr=self.kiosk_cvr,
                product__barcode=self.product_barcode_1,
                location_id=2,
                rvm_serial=int(self.refund_method_1_serial_number),
                barcode=self.product_barcode_1,
                count=20,
            ),
            item(
                deposit_payout__source_identifier="example_with_valid_ids.csv",
                company_branch__company__cvr=None,
                kiosk__cvr=self.kiosk_cvr,
                product__barcode=self.product_barcode_1,
                location_id=2,
                rvm_serial=int(self.refund_method_1_serial_number),
                barcode=self.product_barcode_1,
                count=500,
            ),
        ]
        # Assert: verify that the actual `DepositPayoutItem` objects match the expected
        # objects.
        self.assertQuerySetEqual(
            actual_items, expected_items, transform=dict, ordered=True
        )


class _SourceSubclass(Source):
    """Concrete subclass of `Source`, used for testing the concrete method(s) defined by
    `Source`.
    """

    def listdir(self):
        pass

    def open(self, filename):
        pass


class TestSource(TestCase):
    @classmethod
    def setUpTestData(cls):
        DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_CSV,
            source_identifier="already_processed.csv",
            from_date=datetime.date.today(),
            to_date=datetime.date.today(),
            item_count=0,
        )
        cls._instance = _SourceSubclass()

    def test_get_new_files(self):
        # Arrange
        with patch.object(self._instance, "listdir", return_value=["foo.csv"]):
            # Act
            result = self._instance.get_new_files()
            # Assert
            self.assertEqual(result, {"foo.csv"})

    def test_get_new_files_already_processed(self):
        # Arrange
        with patch.object(
            self._instance, "listdir", return_value=["already_processed.csv"]
        ):
            # Act
            result = self._instance.get_new_files()
            # Assert
            self.assertEqual(result, set())


class TestSFTP(SimpleTestCase):
    """Test the `SFTP` source class"""

    _get_ssh_client = (
        "esani_pantportal.management.commands.import_deposit_payouts.SFTP."
        "_get_ssh_client"
    )

    _sftp_url = "sftp://username:password@host:1234/path/"

    def test_init(self):
        # Arrange
        mock_ssh_client = MagicMock()
        with patch(self._get_ssh_client, return_value=mock_ssh_client):
            # Act
            instance = SFTP(self._sftp_url)
            # Assert: calls to methods on `paramiko.SSHClient`
            mock_ssh_client.set_missing_host_key_policy.assert_called_once_with(ANY)
            mock_ssh_client.connect.assert_called_once_with(
                hostname="host",
                port=1234,
                username="username",
                password="password",
            )
            mock_ssh_client.open_sftp.assert_called_once_with()
            # Assert: calls to methods on `paramiko.SFTPClient`
            instance._ftp.chdir.assert_called_once_with("/path/")

    def test_listdir(self):
        # Arrange
        with patch(self._get_ssh_client):
            instance = SFTP(self._sftp_url)
            with patch.object(instance._ftp, "listdir", return_value=["foo.csv"]):
                # Act
                result = instance.listdir()
                # Assert
                self.assertEqual(result, ["foo.csv"])

    def test_open(self):
        # Arrange
        with patch(self._get_ssh_client):
            instance = SFTP(self._sftp_url)
            # Act
            instance.open("filename.csv")
            # Assert
            instance._ftp.open.assert_called_once_with("filename.csv")


class TestLocalFileSystem(TestCase):
    """Test the `LocalFilesystem` source class"""

    @classmethod
    def setUpTestData(cls):
        cls._instance = LocalFilesystem("path")

    def test_listdir(self):
        # Arrange
        with patch("os.listdir", return_value=["foo.csv"]) as mock_listdir:
            # Act
            result = self._instance.listdir()
            # Assert
            self.assertEqual(result, ["foo.csv"])
            mock_listdir.assert_called_once_with(self._instance._path)

    def test_open(self):
        # Arrange
        with patch("builtins.open", new_callable=mock_open, read_data="data"):
            # Act
            result = self._instance.open("filename.csv")
            # Assert
            self.assertEqual(result.read(), "data")
