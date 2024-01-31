# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from http import HTTPStatus

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
            invoice_mail="foo@bar.com",
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
            invoice_mail="foo@bar.com",
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            municipality="foo",
            branch_type="A",
            customer_id=2,
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
            municipality="foo",
            branch_type="A",
            customer_id=2,
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
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
        return output

    def test_esani_admin_view(self):
        self.login()
        response = self.client.get(reverse("pant:company_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = self.get_html_items(response.content)
        companies = [d["Navn"] for d in data]

        self.assertEqual(len(data), 4)
        self.assertIn(self.facebook.name, companies)
        self.assertIn(self.google.name, companies)
        self.assertIn(self.kiosk.name, companies)
        self.assertIn(self.facebook_branch.name, companies)

    def test_kiosk_admin_view(self):
        self.login("KioskUsers")
        response = self.client.get(reverse("pant:company_list"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


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
            branch=cls.facebook_branch,
        )

    def check_delete_flag(self, pk, object_type):
        # Google can be deleted - it has no related objects
        response = self.client.get(
            reverse(f"pant:update_{object_type}", kwargs={"pk": pk})
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
