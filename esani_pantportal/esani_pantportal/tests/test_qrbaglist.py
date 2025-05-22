# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from http import HTTPStatus

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db.models import F, OrderBy, Sum
from django.test import RequestFactory, TestCase
from django.urls import reverse
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    Kiosk,
    Product,
    QRBag,
    QRStatus,
)
from esani_pantportal.views import (
    QRBagHistoryView,
    QRBagSearchView,
    _get_qr_bag_filtered_annotation,
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

        # Create `QRStatus` objects matching the status codes used in the tests
        for code in ("butik_oprettet", "under_transport"):
            QRStatus.objects.get_or_create(code=code, name_da=code, name_kl=code)

        # Two bags are created by a branch-admin
        qrbag1 = QRBag(
            qr="qr1",
            status="butik_oprettet",
            company_branch=cls.branch1,
            owner=cls.branch_admin,
        )
        qrbag1._history_user = cls.branch_admin
        qrbag1.save()
        qrbag2 = QRBag(
            qr="qr2",
            status="butik_oprettet",
            company_branch=cls.branch1,
            owner=cls.branch_admin,
        )
        qrbag2._history_user = cls.branch_admin
        qrbag2.save()

        # One of them is edited by an ESANI-admin
        qrbag1.status = "under_transport"
        qrbag1._history_user = cls.esani_admin
        qrbag1.save()

        # This QR bag belongs to a kiosk (and branch-admins should therefore not see it)
        qrbag3 = QRBag(qr="qr3", status="butik_oprettet", kiosk=cls.kiosk)
        qrbag3._history_user = cls.esani_admin
        qrbag3.save()

        # This QR bag belongs to another branch in the same company
        qrbag4 = QRBag(qr="qr4", status="butik_oprettet", company_branch=cls.branch2)
        qrbag4._history_user = cls.esani_admin
        qrbag4.save()

        # QR bag 3 has two deposit payout items (both valid)
        cls._add_deposit_payout_item(qrbag3, count=1, valid=True)
        cls._add_deposit_payout_item(qrbag3, count=2, valid=True)

        # QR bag 4 has two deposit payout items (one valid and one invalid)
        cls._add_deposit_payout_item(qrbag4, count=1, valid=True)
        cls._add_deposit_payout_item(qrbag4, count=2, valid=False)

    @staticmethod
    def extract_data_from_table(table):
        headers = [cell.text.strip() for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append({k: v for k, v in dict(zip(headers, rowdata)).items() if k})
        return output

    @classmethod
    def _add_deposit_payout_item(cls, bag: QRBag, count: int = 1, valid: bool = True):
        deposit_payout, _ = DepositPayout.objects.get_or_create(
            source_identifier="QRBagTest",
            defaults={
                "source_type": DepositPayout.SOURCE_TYPE_API,
                "from_date": "2024-01-01",
                "to_date": "2024-02-01",
                "item_count": 1,
            },
        )
        barcode = "barcode"
        product, _ = Product.objects.get_or_create(
            barcode=barcode,
            defaults={
                "product_name": "QRBagTest",
                "refund_value": 200,
                "material": "P",
                "height": 200,
                "diameter": 100,
                "weight": 50,
                "capacity": 200,
                "shape": "F",
            },
        )
        DepositPayoutItem.objects.create(
            deposit_payout=deposit_payout,
            date=date(2024, 1, 1),
            qr_bag=bag,
            count=count,
            product=product if valid else None,
            barcode=barcode if valid else None,
        )


class QRBagListViewTest(ParametrizedTestCase, BaseQRBagTest):
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

        self.assertEqual(bags["qr1"]["Butik"], "branch1")
        self.assertEqual(bags["qr2"]["Butik"], "branch1")
        self.assertEqual(bags["qr3"]["Butik"], "kiosk")
        self.assertEqual(bags["qr4"]["Butik"], "branch2")

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
        choices = dict(response.context["form"].fields["status"].choices)
        self.assertEqual(choices["butik_oprettet"], "butik_oprettet (3)")
        self.assertEqual(choices["under_transport"], "under_transport (1)")

    def test_counts_as_company_admin(self):
        self.client.login(username="company_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        choices = dict(response.context["form"].fields["status"].choices)
        self.assertEqual(choices["butik_oprettet"], "butik_oprettet (2)")
        self.assertEqual(choices["under_transport"], "under_transport (1)")

    def test_annotation_columns(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        self.assertQuerySetEqual(
            response.context["items"],
            [
                # QR bag 1 has no items
                ("qr1", "-", "-", "-"),
                # QR bag 2 has no items
                ("qr2", "-", "-", "-"),
                # QR bag 3 has 2 valid items with count=1 and count=2 (total of 3)
                ("qr3", 3, "-", 6),
                # QR bag 4 has 1 valid item (with count=1) and one invalid item (with
                # count=2)
                ("qr4", 1, 2, 2),
            ],
            transform=lambda obj: (
                obj["qr"],
                obj["num_valid_deposited"],
                obj["num_invalid_deposited"],
                obj["value_of_valid_deposited"],
            ),
            ordered=False,
        )

    def test_get_qr_bag_filtered_annotation(self):
        for valid in (True, False):
            with self.subTest(valid=valid):
                annotation = _get_qr_bag_filtered_annotation(Sum("foo"), valid=valid)
                self.assertEqual(annotation.filter.negated, not valid)

    @parametrize(
        "statuses,expected_result",
        [
            # Test 1: only one status is selected
            (
                ["under_transport"],  # statuses
                [("qr1", "under_transport")],  # expected_results
            ),
            # Test 2: multiple statuses are selected
            (
                ["butik_oprettet", "under_transport"],  # statuses
                [  # expected_results
                    ("qr1", "under_transport"),
                    ("qr2", "butik_oprettet"),
                    ("qr3", "butik_oprettet"),
                    ("qr4", "butik_oprettet"),
                ],
            ),
        ],
    )
    def test_filter_on_multiple_statuses(self, statuses, expected_result):
        # Arrange
        view = self._get_view_instance(status=statuses)
        # Act
        filtered_qs = view.filter_qs(QRBag.objects.all())
        # Assert
        self.assertQuerySetEqual(
            filtered_qs,
            expected_result,
            ordered=False,
            transform=lambda obj: (obj.qr, obj.status),
        )

    @parametrize(
        "sort,order,expected_order_by",
        [
            (
                "num_valid_deposited",
                None,
                (
                    OrderBy(
                        F("num_valid_deposited"), descending=False, nulls_first=True
                    ),
                ),
            ),
            (
                "num_valid_deposited",
                "desc",
                (OrderBy(F("num_valid_deposited"), descending=True, nulls_last=True),),
            ),
        ],
    )
    def test_sort_on_annotation_field(self, sort, order, expected_order_by):
        # Arrange
        view = self._get_view_instance(sort=sort, order=order)
        # Act
        sorted_qs = view.sort_qs(QRBag.objects.all())
        # Assert
        self.assertEqual(sorted_qs.query.order_by, expected_order_by)

    @parametrize(
        "annotation,status,expected_result",
        [
            ("num_valid_deposited", "esani_optalt", 0),
            ("num_valid_deposited", "esani_udbetalt", 0),
            ("num_valid_deposited", "other", "-"),
            ("num_invalid_deposited", "esani_optalt", 0),
            ("num_invalid_deposited", "esani_udbetalt", 0),
            ("num_invalid_deposited", "other", "-"),
        ],
    )
    def test_map_value_displays_annotation_null_value_as_zero(
        self, annotation, status, expected_result
    ):
        view = self._get_view_instance()
        result = view.map_value({"status": status, annotation: None}, annotation, None)
        self.assertEqual(result, expected_result)

    def _get_view_instance(self, **kwargs) -> QRBagSearchView:
        view = QRBagSearchView()
        view.request = RequestFactory().get("")
        view.search_data = kwargs
        return view


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
        self.assertEqual(history_dict["butik_oprettet"], "branch_admin")
        self.assertEqual(history_dict["under_transport"], "esani_admin")

    def test_context_includes_deposit_payout_items(self):
        # Arrange: get history page for QR bag 4
        view = self._get_view_instance("qr4")
        # Act
        context = view.get_context_data()
        # Assert: check "count" and "value" column values
        self.assertQuerySetEqual(
            context["deposit_payout_items"],
            [
                (1, 2),  # item 1 (valid): count=1, value=1 * 2 = 2
                (2, None),  # item 2 (invalid): count=2, value=NULL
            ],
            ordered=False,
            transform=lambda obj: (obj.count, obj.value),
        )
        # Assert: check "total_count" is sum of counts for items 1 and 2
        self.assertEqual(context["total_count"], 1 + 2)
        # Assert: check "total_value"
        self.assertEqual(context["total_value"], (1 * 2) + (2 * 0))

    def _get_view_instance(self, qr: str) -> QRBagHistoryView:
        request = RequestFactory().get("")
        view = QRBagHistoryView()
        view.setup(request, pk=QRBag.objects.get(qr=qr).pk)
        view.get(request)
        return view
