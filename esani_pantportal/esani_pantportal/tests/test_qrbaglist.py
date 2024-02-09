# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from http import HTTPStatus

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    QRBag,
)


class BaseQRBagTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
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

        cls.company = Company.objects.create(
            name="company",
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

        cls.branch1 = CompanyBranch.objects.create(
            company=cls.company,
            name="branch1",
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

        cls.branch2 = CompanyBranch.objects.create(
            company=cls.company,
            name="branch2",
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

        cls.branch_admin = BranchUser.objects.create_user(
            username="branch_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.branch1,
            first_name="Branch",
            last_name="Admin",
        )
        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
        )
        cls.company_admin = CompanyUser.objects.create_user(
            username="company_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.company,
        )

        call_command("create_groups")
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))
        cls.branch_admin.groups.add(Group.objects.get(name="BranchAdmins"))
        cls.company_admin.groups.add(Group.objects.get(name="CompanyAdmins"))

        # Two bags are created by a branch-admin
        qrbag1 = QRBag(
            qr="qr1",
            status="Oprettet",
            company_branch=cls.branch1,
            owner=cls.branch_admin,
        )
        qrbag1._history_user = cls.branch_admin
        qrbag1.save()
        qrbag2 = QRBag(
            qr="qr2",
            status="Oprettet",
            company_branch=cls.branch1,
            owner=cls.branch_admin,
        )
        qrbag2._history_user = cls.branch_admin
        qrbag2.save()

        # One of them is edited by an ESANI-admin
        qrbag1.status = "Under transport"
        qrbag1._history_user = cls.esani_admin
        qrbag1.save()

        # This QR bag belongs to a kiosk (and branch-admins should therefore not see it)
        qrbag3 = QRBag(qr="qr3", status="Oprettet", kiosk=cls.kiosk)
        qrbag3._history_user = cls.esani_admin
        qrbag3.save()

        # This QR bag belongs to another branch in the same company
        qrbag4 = QRBag(qr="qr4", status="Oprettet", company_branch=cls.branch2)
        qrbag4._history_user = cls.esani_admin
        qrbag4.save()

    @staticmethod
    def extract_data_from_table(table):
        headers = [cell.text for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append({k: v for k, v in dict(zip(headers, rowdata)).items() if k})
        return output


class QRBagListViewTest(BaseQRBagTest):
    def get_html_items(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(attrs={"id": "table"})
        return self.extract_data_from_table(table)

    def get_bags(self):
        response = self.client.get(reverse("pant:qrbag_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        html_items = self.get_html_items(response.content)

        bags = {item["QR kode"]: item for item in html_items}
        return bags

    def test_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        bags = self.get_bags()
        self.assertEqual(len(bags), 4)  # ESani admin can see all bags

        self.assertEqual(bags["qr1"]["Ejer"], "Branch Admin")
        self.assertEqual(bags["qr2"]["Ejer"], "Branch Admin")
        self.assertEqual(bags["qr3"]["Ejer"], "-")
        self.assertEqual(bags["qr4"]["Ejer"], "-")

        self.assertEqual(bags["qr1"]["Butik"], "branch1")
        self.assertEqual(bags["qr2"]["Butik"], "branch1")
        self.assertEqual(bags["qr3"]["Butik"], "kiosk")
        self.assertEqual(bags["qr4"]["Butik"], "branch2")

        self.assertEqual(bags["qr1"]["Status"], "Under transport")
        self.assertEqual(bags["qr2"]["Status"], "Oprettet")
        self.assertEqual(bags["qr3"]["Status"], "Oprettet")
        self.assertEqual(bags["qr4"]["Status"], "Oprettet")

    def test_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        bags = self.get_bags()
        self.assertEqual(len(bags), 3)  # Company admin cannot see the kiosk-bag

    def test_branch_admin_view(self):
        self.client.login(username="branch_admin", password="12345")
        bags = self.get_bags()
        self.assertEqual(len(bags), 2)  # Branch admin can only see from his own branch

    def test_counts_as_esani_admin(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        count = response.context["status_dict"]
        self.assertEqual(count["Oprettet"], 3)
        self.assertEqual(count["Under transport"], 1)

    def test_counts_as_company_admin(self):
        self.client.login(username="company_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        count = response.context["status_dict"]
        self.assertEqual(count["Oprettet"], 2)
        self.assertEqual(count["Under transport"], 1)


class QRBagHistoryViewTest(BaseQRBagTest):
    def get_html_items(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        return self.extract_data_from_table(table)

    def test_history(self):
        self.client.login(username="esani_admin", password="12345")
        qrbag_with_history = QRBag.objects.get(qr="qr1")

        response = self.client.get(
            reverse("pant:qrbag_history", kwargs={"pk": qrbag_with_history.pk})
        )

        histories = self.get_html_items(response.content)
        self.assertEqual(len(histories), 2)

        history_dict = {h["Status"]: h["Ændringsansvarlig"] for h in histories}
        self.assertEqual(history_dict["Oprettet"], "branch_admin")
        self.assertEqual(history_dict["Under transport"], "esani_admin")
