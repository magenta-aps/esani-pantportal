# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from csv import DictReader
from http import HTTPStatus
from io import StringIO

from bs4 import BeautifulSoup
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import (
    Company,
    CompanyBranch,
    Kiosk,
    KioskUser,
    ReverseVendingMachine,
)

from .conftest import LoginMixin


class BaseCompanyTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            country="USA",
            phone="+4544457845",
            company_type="E",
            registration_number="112",
            account_number="112",
            invoice_mail="fb@bar.com",
            invoice_company_branch=True,
        )

        cls.google = Company.objects.create(
            name="google",
            cvr=12312346,
            address="foo",
            postal_code="123",
            city="test city",
            country="USA",
            phone="+4544457845",
            company_type="A",
            registration_number="112",
            account_number="112",
            invoice_mail="gl@bar.com",
            invoice_company_branch=False,
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=100,
            municipality="foo",
            branch_type="A",
            customer_id=2,
            registration_number="112",
            account_number="112",
            invoice_mail="fbb@bar.com",
            qr_compensation=2,
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=200,
            cvr=11221122,
            municipality="foo",
            branch_type="A",
            customer_id=3,
            registration_number="112",
            account_number="112",
            invoice_mail="kio@bar.com",
            qr_compensation=2.5,
        )


class CompanyListTest(BaseCompanyTest):
    @staticmethod
    def get_html_items(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        headers = [cell.text for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append({k: v for k, v in dict(zip(headers, rowdata)).items() if k})

        return {o["Navn"]: o for o in output}

    @staticmethod
    def get_table_headers(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        return [
            cell.attrs.get("data-field")
            for cell in table.thead.tr.find_all("th")
            if cell.attrs.get("data-visible", "true") == "true"
        ]

    def test_esani_admin_view(self):
        self.login()
        response = self.client.get(reverse("pant:company_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        companies = self.get_html_items(response.content)

        self.assertEqual(len(companies), 4)
        self.assertIn(self.facebook.name, companies)
        self.assertIn(self.google.name, companies)
        self.assertIn(self.kiosk.name, companies)
        self.assertIn(self.facebook_branch.name, companies)

        self.assertEqual(companies["kiosk"]["Butikstype"], "Andet")
        self.assertEqual(companies["facebook_branch"]["Butikstype"], "Andet")
        self.assertEqual(companies["google"]["Butikstype"], "-")
        self.assertEqual(companies["facebook"]["Butikstype"], "-")

        self.assertEqual(companies["kiosk"]["Virksomhedstype"], "-")
        self.assertEqual(companies["facebook_branch"]["Virksomhedstype"], "-")
        self.assertEqual(companies["google"]["Virksomhedstype"], "Andet")
        self.assertEqual(companies["facebook"]["Virksomhedstype"], "Eksportør")

        self.assertEqual(companies["kiosk"]["Kommune"], "foo")
        self.assertEqual(companies["facebook_branch"]["Kommune"], "foo")
        self.assertEqual(companies["google"]["Kommune"], "-")
        self.assertEqual(companies["facebook"]["Kommune"], "-")

        self.assertEqual(companies["kiosk"]["Virksomhed"], "-")
        self.assertEqual(companies["facebook_branch"]["Virksomhed"], "facebook")
        self.assertEqual(companies["google"]["Virksomhed"], "-")
        self.assertEqual(companies["facebook"]["Virksomhed"], "-")

        self.assertEqual(companies["kiosk"]["Kunde ID"], "3")
        self.assertEqual(companies["facebook_branch"]["Kunde ID"], "2")
        self.assertEqual(companies["google"]["Kunde ID"], "-")
        self.assertEqual(companies["facebook"]["Kunde ID"], "-")

        self.assertEqual(companies["kiosk"]["Lokation ID"], "200")
        self.assertEqual(companies["facebook_branch"]["Lokation ID"], "100")
        self.assertEqual(companies["google"]["Lokation ID"], "-")
        self.assertEqual(companies["facebook"]["Lokation ID"], "-")

        self.assertEqual(companies["kiosk"]["CVR"], "11221122")
        self.assertEqual(companies["facebook_branch"]["CVR"], "-")
        self.assertEqual(companies["google"]["CVR"], "12312346")
        self.assertEqual(companies["facebook"]["CVR"], "12312345")

        self.assertEqual(companies["kiosk"]["Faktura til butik"], "-")
        self.assertEqual(companies["facebook_branch"]["Faktura til butik"], "-")
        self.assertEqual(companies["google"]["Faktura til butik"], "Nej")
        self.assertEqual(companies["facebook"]["Faktura til butik"], "Ja")

        self.assertEqual(companies["kiosk"]["Fakturamail"], "kio@bar.com")
        self.assertEqual(companies["facebook_branch"]["Fakturamail"], "fbb@bar.com")
        self.assertEqual(companies["google"]["Fakturamail"], "gl@bar.com")
        self.assertEqual(companies["facebook"]["Fakturamail"], "fb@bar.com")

        self.assertEqual(
            companies["kiosk"]["Håndterings-godtgørelse for QR-poser"], "2.5 øre"
        )
        self.assertEqual(
            companies["facebook_branch"]["Håndterings-godtgørelse for QR-poser"],
            "2 øre",
        )
        self.assertEqual(
            companies["google"]["Håndterings-godtgørelse for QR-poser"], "-"
        )
        self.assertEqual(
            companies["facebook"]["Håndterings-godtgørelse for QR-poser"],
            "-",
        )

    def test_kiosk_admin_view(self):
        self.login("KioskUsers")
        response = self.client.get(reverse("pant:company_list"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_external_customer_id(self):
        def prefix(external_customer_id):
            return external_customer_id.split("-")[0]

        self.login()
        response = self.client.get(reverse("pant:company_list"))
        ext_id_and_names = [
            (item.external_customer_id_annotation, item.name)
            for item in response.context["items"]
        ]
        self.assertListEqual(
            [(prefix(elem[0]), elem[1]) for elem in ext_id_and_names],
            [
                (Company.customer_id_prefix, self.facebook.name),
                (CompanyBranch.customer_id_prefix, self.facebook_branch.name),
                (Company.customer_id_prefix, self.google.name),
                (Kiosk.customer_id_prefix, self.kiosk.name),
            ],
        )

    def test_column_preferences(self):
        # Load the page with default settings
        user = self.login()
        response = self.client.get(reverse("pant:company_list"))
        data = self.get_table_headers(response.content)
        self.assertIn("municipality", data)

        # Edit preferences
        self.client.post(
            reverse("pant:preferences_update", kwargs={"pk": user.pk}),
            data={"show_company_municipality": "false"},
        )

        # Reload the page
        response = self.client.get(reverse("pant:product_list"))
        data = self.get_table_headers(response.content)
        self.assertNotIn("municipality", data)


class CompanyDeleteTest(BaseCompanyTest):
    def setUp(self):
        self.login()

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        # Add user to kiosk (so the kiosk cannot be deleted)
        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.kiosk,
        )

        # Add refund machine to facebook_branch (so facebook branch cannot be deleted)
        cls.facebook_branch_rvm = ReverseVendingMachine.objects.create(
            compensation=300,
            serial_number="",
            company_branch=cls.facebook_branch,
        )

    def check_delete_flag(self, pk, object_type):
        # Google can be deleted - it has no related objects
        response = self.client.get(
            reverse(f"pant:{object_type}_update", kwargs={"pk": pk})
        )
        self.assertTrue(response.context_data["can_delete"])

    def test_delete_company(self):
        # Google can be deleted - it has no related objects
        pk = self.google.pk
        self.assertTrue(Company.objects.filter(pk=pk).exists())
        self.check_delete_flag(pk, "company")
        response = self.client.post(reverse("pant:company_delete", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Company.objects.filter(pk=pk).exists())

    def test_delete_company_with_branch(self):
        # Facebook cannot be deleted - because it has a branch
        pk = self.facebook.pk
        self.assertTrue(Company.objects.filter(pk=pk).exists())
        with self.assertRaises(ProtectedError):
            self.client.post(reverse("pant:company_delete", kwargs={"pk": pk}))

        # Removing the branch allows deleting the company
        self.facebook_branch_rvm.delete()
        self.facebook_branch.delete()
        self.check_delete_flag(pk, "company")
        response = self.client.post(reverse("pant:company_delete", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Company.objects.filter(pk=pk).exists())

    def test_delete_company_branch_with_refund_machine(self):
        # The facebook branch cannot be deleted - because it has a refund machine
        pk = self.facebook_branch.pk
        self.assertTrue(CompanyBranch.objects.filter(pk=pk).exists())
        with self.assertRaises(ProtectedError):
            self.client.post(reverse("pant:company_branch_delete", kwargs={"pk": pk}))

        # Removing the refund machine allows deleting the branch
        self.facebook_branch_rvm.delete()
        self.check_delete_flag(pk, "company_branch")
        response = self.client.post(
            reverse("pant:company_branch_delete", kwargs={"pk": pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(CompanyBranch.objects.filter(pk=pk).exists())

    def test_delete_kiosk_with_user(self):
        # The kiosk cannot be deleted, because it has a user
        pk = self.kiosk.pk
        self.assertTrue(Kiosk.objects.filter(pk=pk).exists())
        with self.assertRaises(ProtectedError):
            self.client.post(reverse("pant:kiosk_delete", kwargs={"pk": pk}))

        # Removing the user allows deleting the kiosk
        self.kiosk_admin.delete()
        self.check_delete_flag(pk, "kiosk")
        response = self.client.post(reverse("pant:kiosk_delete", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Kiosk.objects.filter(pk=pk).exists())


class CompanyListExportTest(BaseCompanyTest):
    def test_export(self):
        # Fetch debtor list as CSV
        self.login()
        response = self.client.get(reverse("pant:all_companies_csv_download"))
        # Assert we get the expected response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertRegex(
            response["Content-Disposition"],
            r"attachment; filename=(.*?)_all_companies\.csv",
        )
        # Assert that all companies, company branches and kiosks defined in this test
        # are exported in the CSV.
        self.assertSetEqual(
            {
                row["name"]
                for row in DictReader(
                    StringIO(response.content.decode("utf-8")), delimiter=";"
                )
            },
            {
                obj.name
                for obj in (
                    self.google,
                    self.facebook,
                    self.facebook_branch,
                    self.kiosk,
                )
            },
        )

    def test_debtor_export(self):
        # Fetch debtor list as CSV
        self.login()
        response = self.client.get(reverse("pant:all_companies_csv_debtor_download"))
        # Assert we get the expected response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertRegex(
            response["Content-Disposition"],
            r"attachment; filename=debitor_(.*?)\.csv",
        )
        # Assert that all companies, company branches and kiosks defined in this test
        # are exported in the CSV.
        self.assertSetEqual(
            {
                row["name"]
                for row in DictReader(
                    StringIO(response.content.decode("utf-8")), delimiter=";"
                )
            },
            {
                obj.name
                for obj in (
                    self.google,
                    self.facebook,
                    self.facebook_branch,
                    self.kiosk,
                )
            },
        )
