# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import io
import os
from http import HTTPStatus
from io import StringIO
from unittest.mock import MagicMock, call, patch

import pandas as pd
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from metrics.job import JOB_EXEC_TIME_REGISTRY

from esani_pantportal.models import (
    BRANCH_USER,
    COMPANY_USER,
    ESANI_USER,
    KIOSK_USER,
    AbstractCompany,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    Kiosk,
    KioskUser,
    Product,
    User,
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
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod1.approve()
        cls.prod1.save()

        cls.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2.approve()
        cls.prod2.save()

        cls.prod3 = Product.objects.create(
            product_name="prod3",
            barcode="0003",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        cls.prod4 = Product.objects.create(
            product_name="prod4",
            barcode="0004",
            refund_value=3,
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

    @patch("metrics.job.push_to_gateway")
    def test_csv_export(self, mock_push_to_gateway: MagicMock):
        filename = self.call_command(".")
        self.assertIn(filename, os.listdir("."))

        df = pd.read_csv(filename, sep=";", dtype={"Barcode": str})
        self.assertEqual(len(df), 2)  # There are two approved products
        self.assertEqual(list(df.loc[:, "Barcode"]), ["0010", "0002"])

        mock_push_to_gateway.assert_called_with(
            settings.PROMETHEUS_PUSHGATEWAY_HOST,
            job="export_approved_products_to_csv",
            registry=JOB_EXEC_TIME_REGISTRY,
        )

    @patch("metrics.job.push_to_gateway")
    @patch(
        "esani_pantportal.management.commands."
        "export_approved_products_to_csv.datetime",
        datetime_mock,
    )
    def test_csv_export_cleanup(self, mock_push_to_gateway: MagicMock):
        # Export three csv files
        filenames = []
        for i in range(3):
            filename = self.call_command(".", max_number_of_files=2)
            filenames.append(filename)

        # Validate that the first one is cleaned up
        self.assertNotIn(filenames[0], os.listdir("."))
        self.assertIn(filenames[1], os.listdir("."))
        self.assertIn(filenames[2], os.listdir("."))

        mock_push_to_gateway.assert_has_calls(
            [
                call(
                    settings.PROMETHEUS_PUSHGATEWAY_HOST,
                    job="export_approved_products_to_csv",
                    registry=JOB_EXEC_TIME_REGISTRY,
                )
                for i in range(3)
            ]
        )


class CSVExportViewTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_company = Company.objects.create(
            name="test-company",
            cvr=10000000,
            address="Væskevej 1337",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            country="Grønland",
            company_type="A",
        )
        cls.company_user = CompanyUser.objects.create_user(
            username="testuser_CompanyUsers",
            password="12345",
            email="test-company-admins@test.com",
            company_id=cls.test_company.id,
        )

        cls.test_branch = CompanyBranch.objects.create(
            company=cls.test_company,
            name="test-branch",
            address="Væskevej 1337",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            location_id=1,
        )
        cls.branch_user = BranchUser.objects.create_user(
            branch=cls.test_branch,
            username="testuser_BranchUsers",
            password="12345",
            email="test-branch-admins@test.com",
        )

        cls.test_kiosk_branch = Kiosk.objects.create(
            cvr=10000000,
            name="test-kiosk",
            address="Væskevej 1337",
            municipality="Aarhus",
            city="Nuuk",
            postal_code="1234",
            phone="(+299) 363542",
            location_id=1,
            registration_number=123,
            account_number=234,
            invoice_mail="foo@bar.com",
        )
        cls.kiosk_user = KioskUser.objects.create_user(
            branch=cls.test_kiosk_branch,
            username="testuser_KioskUsers",
            password="12345",
            email="test-kiosk-admins@test.com",
        )


class CSVExportUsersViewTest(CSVExportViewTest):
    company_fields = [f.name for f in AbstractCompany._meta.fields]
    user_fields = [f.name for f in User._meta.fields if f.name != "password"]

    user_type_map = {
        ESANI_USER: "ESANI_USER",
        BRANCH_USER: "BRANCH_USER",
        COMPANY_USER: "COMPANY_USER",
        KIOSK_USER: "KIOSK_USER",
    }

    def assert_contents_equal(self, field_csv_value, field_obj_value):
        if type(field_obj_value) is datetime.datetime:
            field_obj_value = field_obj_value.isoformat()
            field_csv_value = datetime.datetime.fromisoformat(
                field_csv_value
            ).isoformat()

        if field_obj_value or type(field_obj_value) is bool:
            self.assertEqual(field_csv_value, field_obj_value)
        else:
            self.assertTrue(pd.isnull(field_csv_value))

    def assert_company_fields(self, df, user_id, company):
        """
        Assert that all company cells contain the expected data
        """
        for field in self.company_fields:
            field_csv_value = df.loc[user_id, f"company_{field}"]
            field_obj_value = getattr(company, field)
            self.assert_contents_equal(field_csv_value, field_obj_value)

    def assert_user_fields(self, df, user):
        """
        Assert that all user cells contain the expected data
        """
        for field in self.user_fields:
            field_csv_value = df.loc[user.id, field]
            field_obj_value = getattr(user, field)

            if field == "user_type":
                field_obj_value = self.user_type_map.get(field_obj_value)

            self.assert_contents_equal(field_csv_value, field_obj_value)

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

    def test_contents(self):
        esani_user = self.login()
        esani_user.refresh_from_db()
        response = self.client.get(reverse("pant:all_users_csv_download"))

        data = io.StringIO(str(response.content, "utf-8"))
        dtype = {"company_postal_code": str}
        df = pd.read_csv(data, sep=";", index_col="id", dtype=dtype)
        df["id"] = df.index

        self.assert_company_fields(df, self.kiosk_user.id, self.test_kiosk_branch)
        self.assert_company_fields(df, self.branch_user.id, self.test_branch)
        self.assert_company_fields(df, self.company_user.id, self.test_company)

        self.assertEqual(df.loc[esani_user.id, "company_name"], "ESANI")
        for field in [f for f in self.company_fields if f != "name"]:
            self.assertTrue(pd.isnull(df.loc[esani_user.id, f"company_{field}"]))

        self.assert_user_fields(df, self.kiosk_user)
        self.assert_user_fields(df, self.branch_user)
        self.assert_user_fields(df, self.company_user)
        self.assert_user_fields(df, esani_user)
