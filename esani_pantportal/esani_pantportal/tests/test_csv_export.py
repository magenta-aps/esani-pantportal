# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import os
from http import HTTPStatus
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    Kiosk,
    KioskUser,
    Product,
)

from .conftest import LoginMixin

datetime_mock = MagicMock()
datetime_mock.datetime.now.side_effect = [
    datetime.datetime(2021, 1, 1),
    datetime.datetime(2021, 1, 2),
    datetime.datetime(2021, 1, 3),
]
datetime_mock.datetime.strptime = datetime.datetime.strptime


class ExportProductsToCSVTests(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command("export_approved_products_to_csv", *args, **kwargs, stdout=out)
        return out.getvalue().strip()

    @classmethod
    def setUpTestData(cls):
        cls.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        cls.prod3 = Product.objects.create(
            product_name="prod3",
            barcode="0003",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    def setUp(self):
        for file in os.listdir("."):
            if file.endswith(".csv"):
                os.remove(file)

    def test_csv_export(self):
        filename = self.call_command(".")
        self.assertIn(filename, os.listdir("."))

        df = pd.read_csv(filename, sep=";", dtype={"Barcode": str})
        self.assertEqual(len(df), 2)  # There are two approved products
        self.assertEqual(list(df.loc[:, "Barcode"]), ["0010", "0002"])

    @patch(
        "esani_pantportal.management.commands."
        "export_approved_products_to_csv.datetime",
        datetime_mock,
    )
    def test_csv_export_cleanup(self):
        # Export three csv files
        filenames = []
        for i in range(3):
            filename = self.call_command(".", max_number_of_files=2)
            filenames.append(filename)

        # Validate that the first one is cleaned up
        self.assertNotIn(filenames[0], os.listdir("."))
        self.assertIn(filenames[1], os.listdir("."))
        self.assertIn(filenames[2], os.listdir("."))


class CSVExportViewTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        test_company = Company.objects.create(
            name="test-company",
            cvr=10000000,
            address="Væskevej 1337",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            country="Grønland",
            company_type="A",
        )
        _ = CompanyUser.objects.create_user(
            username="testuser_CompanyUsers",
            password="12345",
            email="test-company-admins@test.com",
            company_id=test_company.id,
        )

        test_branch = CompanyBranch.objects.create(
            company=test_company,
            name="test-branch",
            address="Væskevej 1337",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            location_id=1,
        )
        _ = BranchUser.objects.create_user(
            branch=test_branch,
            username="testuser_BranchUsers",
            password="12345",
            email="test-branch-admins@test.com",
        )

        test_kiosk_branch = Kiosk.objects.create(
            cvr=10000000,
            name="test-kiosk",
            address="Væskevej 1337",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            location_id=1,
        )
        _ = KioskUser.objects.create_user(
            branch=test_kiosk_branch,
            username="testuser_KioskUsers",
            password="12345",
            email="test-kiosk-admins@test.com",
        )


class CSVExportUsersViewTest(CSVExportViewTest):
    def test_admin_user(self):
        self.login()
        url = reverse("pant:all_users_csv_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_company_user(self):
        self.login("CompanyUsers")
        url = reverse("pant:all_users_csv_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_branch_user(self):
        self.login("BranchUsers")
        url = reverse("pant:all_users_csv_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_kiosk_user(self):
        self.login("KioskUsers")
        url = reverse("pant:all_users_csv_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
