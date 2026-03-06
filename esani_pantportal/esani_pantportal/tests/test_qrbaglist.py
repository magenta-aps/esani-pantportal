# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from http import HTTPStatus
from json import loads as load_json

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db.models import F, OrderBy, Sum
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.html import strip_tags
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
from esani_pantportal.tests.conftest import LoginMixin
from esani_pantportal.views import (
    QRBagHistoryView,
    QRBagSearchView,
    _get_qr_bag_filtered_annotation,
)


class BaseQRBagTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city=cls._test_town,
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
            city=cls._test_city,
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
            city=cls._test_town,
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
            city=cls._test_town,
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
        for code in ("butik_oprettet", "under_transport", "esani_skjult"):
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

        # This QR bag has manual deposit payout items
        qrbag5 = QRBag(qr="qr5", status="butik_oprettet", company_branch=cls.branch2)
        qrbag5._history_user = cls.esani_admin
        qrbag5.save()

        # This QR bag has status "hidden"
        qrbag6 = QRBag(qr="qr6", status="esani_skjult", company_branch=cls.branch2)
        qrbag6._history_user = cls.esani_admin
        qrbag6.save()

        # QR bag 3 has two deposit payout items (both valid)
        cls._add_deposit_payout_item(qrbag3, count=1, valid=True)
        cls._add_deposit_payout_item(qrbag3, count=2, valid=True)

        # QR bag 4 has two deposit payout items (one valid and one invalid)
        cls._add_deposit_payout_item(qrbag4, count=1, valid=True)
        cls._add_deposit_payout_item(qrbag4, count=2, valid=False)

        # QR bag 5 has manual deposit payout items
        cls._add_deposit_payout_item(qrbag5, count=4, manual=True)

    @staticmethod
    def extract_data_from_table(table):
        headers = [cell.text.strip() for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append({k: v for k, v in dict(zip(headers, rowdata)).items() if k})
        return output

    @classmethod
    def _add_deposit_payout_item(
        cls,
        bag: QRBag,
        count: int = 1,
        valid: bool = True,
        manual: bool = False,
    ):
        deposit_payout, _ = DepositPayout.objects.get_or_create(
            source_identifier="QRBagTest",
            defaults={
                "source_type": DepositPayout.SOURCE_TYPE_API,
                "from_date": "2024-01-01",
                "to_date": "2024-02-01",
                "item_count": 1,
            },
        )
        barcode = "manual" if manual else "barcode"
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
            rvm_serial=0 if manual else -1,
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
        self.assertEqual(len(bags), 6)  # Esani admin can see all bags
        self.assertEqual(bags["qr1"]["Butik"], "branch1")
        self.assertEqual(bags["qr2"]["Butik"], "branch1")
        self.assertEqual(bags["qr3"]["Butik"], "kiosk")
        self.assertEqual(bags["qr4"]["Butik"], "branch2")
        self.assertEqual(bags["qr5"]["Butik"], "branch2")
        self.assertEqual(bags["qr6"]["Butik"], "branch2")

    def test_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        bags = self.get_bags()
        # Company admin cannot see the kiosk bag
        # Company admin cannot see the hidden bag
        self.assertEqual(len(bags), 4)

    def test_branch_admin_view(self):
        self.client.login(username="branch_admin", password="12345")
        bags = self.get_bags()
        # Branch admin can only see from his own branch
        # Branch admin cannot see the hidden bag
        self.assertEqual(len(bags), 2)

    def test_counts_as_esani_admin(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        choices = dict(response.context["form"].fields["status"].choices)
        self.assertEqual(choices["butik_oprettet"], "butik_oprettet (4)")
        self.assertEqual(choices["under_transport"], "under_transport (1)")
        self.assertEqual(choices["esani_skjult"], "esani_skjult (1)")

    def test_counts_as_company_admin(self):
        self.client.login(username="company_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        choices = dict(response.context["form"].fields["status"].choices)
        self.assertEqual(choices["butik_oprettet"], "butik_oprettet (3)")
        self.assertEqual(choices["under_transport"], "under_transport (1)")
        self.assertNotIn("esani_skjult", choices)

    def test_annotation_columns(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:qrbag_list"))
        self.assertQuerySetEqual(
            response.context["items"],
            [
                # QR bag 1 has no items
                ("qr1", "-", "-", "-", "-"),
                # QR bag 2 has no items
                ("qr2", "-", "-", "-", "-"),
                # QR bag 3 has 2 valid items with count=1 and count=2 (total of 3)
                ("qr3", 3, "-", 6, "-"),
                # QR bag 4 has 1 valid item (with count=1) and one invalid item (with
                # count=2)
                ("qr4", 1, 2, 2, "-"),
                # QR bag 5 has 1 manual item (with count=4)
                ("qr5", 4, "-", 8, "&check;"),
                # QR bag 6 has no items
                ("qr6", "-", "-", "-", "-"),
            ],
            transform=lambda obj: (
                obj["qr"],
                self._clean_value(obj["num_valid_deposited"]),
                obj["num_invalid_deposited"],
                obj["value_of_valid_deposited"],
                obj["manual"],
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
                # statuses
                ["under_transport"],
                # expected_results
                [("qr1", "under_transport")],
            ),
            # Test 2: multiple statuses are selected
            (
                # statuses
                ["butik_oprettet", "under_transport", "esani_skjult"],
                # expected_results
                [
                    ("qr1", "under_transport"),
                    ("qr2", "butik_oprettet"),
                    ("qr3", "butik_oprettet"),
                    ("qr4", "butik_oprettet"),
                    ("qr5", "butik_oprettet"),
                    ("qr6", "esani_skjult"),
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
        result = self._clean_value(
            view.map_value({"status": status, annotation: None}, annotation, None)
        )
        self.assertEqual(result, expected_result)

    @parametrize(
        "qr,expected",
        [
            # Case 1: very long search input matches QR code (`iexact`)
            ("1234567890ABCDabcd", ["1234567890abcdabcd"]),
            # Case 2: medium-length search input matches QR code prefix (`istartswith`)
            ("1234567890", ["1234567890abcdabcd"]),
            # Case 3: medium-length search input matches QR code suffix (`iendswith`)
            ("0ABCDabcd", ["1234567890abcdabcd"]),
            # Case 4: very short search input `r1` matches QR code `qr1` (`icontains`)
            ("r1", ["qr1"]),
        ],
    )
    def test_search_on_qr_varies_with_search_input_length(self, qr, expected):
        # Arrange: add QR bags with medium and long QR codes
        QRBag.objects.get_or_create(qr="1234567890abcdabcd")  # 10+8 digits QR
        # Arrange
        view = self._get_view_instance(qr=qr)
        # Act: get filtered queryset
        qs = view.filter_qs(QRBag.objects.all())
        # Assert: filtered queryset matches expected QR codes
        self.assertQuerySetEqual(
            qs,
            expected,
            transform=lambda obj: obj.qr,
        )

    def test_post_invalid(self):
        data = {"amount": "invalid"}
        view = QRBagSearchView()
        request = RequestFactory().post("", data=data)
        response = view.post(request)
        self.assertEqual(response.status_code, 400)

    def test_post_valid_empty_bag(self):
        # QR bag 1 has no existing deposit payout items, so it is ok to post an amount
        qr_bag_1 = QRBag.objects.get(qr="qr1")
        data = {"id": qr_bag_1.pk, "amount": 42}
        view = QRBagSearchView()
        request = RequestFactory().post("", data=data)
        response = view.post(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(load_json(response.content), {"status": "ok", "amount": 42})
        self.assertEqual(
            (
                DepositPayout.objects.filter(
                    source_identifier="Manual entry for QR bag qr1"
                ).count()
            ),
            1,
        )
        self.assertQuerySetEqual(
            DepositPayoutItem.objects.filter(qr_bag=qr_bag_1).values(
                "company_branch",
                "kiosk",
                "count",
                "date",
                "rvm_serial",
                "product__barcode",
                "barcode",
                "consumer_identity",
            ),
            [
                {
                    "company_branch": qr_bag_1.company_branch.pk,
                    "kiosk": qr_bag_1.kiosk,
                    "count": 42,
                    "date": date.today(),
                    "rvm_serial": "0",
                    "product__barcode": "manual",
                    "barcode": "manual",
                    "consumer_identity": qr_bag_1.qr,
                }
            ],
        )

    def test_post_valid_used_bag(self):
        # QR bag 4 has some existing deposit payout items, so it is not ok to post new
        # amount.
        data = {"id": QRBag.objects.get(qr="qr4").pk, "amount": 42}
        view = QRBagSearchView()
        request = RequestFactory().post("", data=data)
        response = view.post(request)
        self.assertEqual(response.status_code, 400)

    def _get_view_instance(self, **kwargs) -> QRBagSearchView:
        view = QRBagSearchView()
        view.request = RequestFactory().get("")
        view.search_data = kwargs
        return view

    def _clean_value(self, val: str) -> int | str:
        stripped = strip_tags(val).strip()
        return int(stripped) if stripped != "-" else stripped


class QRBagHistoryViewTest(ParametrizedTestCase, BaseQRBagTest):
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

    @parametrize(
        "username,expected_response",
        [
            ("esani_admin", HTTPStatus.OK),
            ("branch_admin", HTTPStatus.FORBIDDEN),
            ("company_admin", HTTPStatus.FORBIDDEN),
        ],
    )
    def test_non_esani_admins_cannot_see_hidden_qrbag(
        self, username, expected_response
    ):
        hidden_qrbag = QRBag.objects.get(qr="qr6")
        self.client.login(username=username, password="12345")
        response = self.client.get(
            reverse("pant:qrbag_history", kwargs={"pk": hidden_qrbag.pk})
        )
        self.assertEqual(response.status_code, expected_response)

    def _get_view_instance(self, qr: str) -> QRBagHistoryView:
        request = RequestFactory().get("")
        view = QRBagHistoryView()
        view.setup(request, pk=QRBag.objects.get(qr=qr).pk)
        view.get(request)
        return view


class TestMultipleQRBagHideView(ParametrizedTestCase, BaseQRBagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.visible_bag = QRBag.objects.get(qr="qr5")
        cls.hidden_bag = QRBag.objects.get(qr="qr6")
        cls.post_data = {
            "ids[]": [cls.visible_bag.id, cls.hidden_bag.id],
            "reason": "Min begrundelse",
        }

    def test_esani_admin_can_hide_multiple(self):
        self.user = self.login("EsaniAdmins")
        response = self.client.post(reverse("pant:qrbag_multiple_hide"), self.post_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json(),
            {
                "total": 2,
                "updated": 1,
                "status_choices": [
                    {"value": "", "label": "-"},
                    {"value": "butik_oprettet", "label": "butik_oprettet (3)"},
                    {"value": "esani_skjult", "label": "esani_skjult (2)"},
                    {"value": "under_transport", "label": "under_transport (1)"},
                ],
            },
        )
        # Assert: visible bag is hidden
        self.visible_bag.refresh_from_db()
        self.assertEqual(self.visible_bag.status, "esani_skjult")
        self.assertEqual(self.visible_bag.hidden_reason, "Min begrundelse")
        # Assert: hidden bag remains unchanged
        self.hidden_bag.refresh_from_db()
        self.assertEqual(self.hidden_bag.status, "esani_skjult")
        self.assertIsNone(self.hidden_bag.hidden_reason)

    def test_non_esani_admin_cannot_hide_multiple(self):
        self.user = self.login("BranchAdmins")
        response = self.client.post(reverse("pant:qrbag_multiple_hide"), self.post_data)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        # Assert: visible bag remains unchanged
        self.visible_bag.refresh_from_db()
        self.assertEqual(self.visible_bag.status, "butik_oprettet")
        self.assertIsNone(self.visible_bag.hidden_reason)
        # Assert: hidden bag remains unchanged
        self.hidden_bag.refresh_from_db()
        self.assertEqual(self.hidden_bag.status, "esani_skjult")
        self.assertIsNone(self.hidden_bag.hidden_reason)


class TestMultipleQRBagUnhideView(ParametrizedTestCase, BaseQRBagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.visible_bag = QRBag.objects.get(qr="qr5")
        cls.hidden_bag = QRBag.objects.get(qr="qr6")

        # Add history entries to hidden bag
        for status in ("under_transport", "esani_skjult"):
            cls.hidden_bag.status = status
            cls.hidden_bag._history_user = cls.esani_admin
            cls.hidden_bag.save()  # adds history entry

        # Add hidden bag without previous history
        cls.hidden_bag_no_history = QRBag(
            qr="qr7", status="esani_skjult", company_branch=cls.branch2
        )
        cls.hidden_bag_no_history._history_user = cls.esani_admin
        cls.hidden_bag_no_history.save()

        cls.post_data = {
            "ids[]": [
                cls.visible_bag.id,
                cls.hidden_bag.id,
                cls.hidden_bag_no_history.id,
            ]
        }

    def test_esani_admin_can_unhide_multiple(self):
        self.user = self.login("EsaniAdmins")
        response = self.client.post(
            reverse("pant:qrbag_multiple_unhide"), self.post_data
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json(),
            {
                "total": 3,
                "updated": 2,
                "status_choices": [
                    {"value": "", "label": "-"},
                    {"value": "butik_oprettet", "label": "butik_oprettet (5)"},
                    {"value": "under_transport", "label": "under_transport (2)"},
                ],
            },
        )
        # Assert: hidden bag is returned to its former status
        self.hidden_bag.refresh_from_db()
        self.assertEqual(self.hidden_bag.status, "under_transport")
        self.assertIsNone(self.hidden_bag.hidden_reason)
        # Assert: hidden bag without history is returned to the default status
        self.hidden_bag_no_history.refresh_from_db()
        self.assertEqual(self.hidden_bag_no_history.status, "butik_oprettet")
        self.assertIsNone(self.hidden_bag_no_history.hidden_reason)
        # Assert: visible bag remains unchanged
        self.visible_bag.refresh_from_db()
        self.assertEqual(self.visible_bag.status, "butik_oprettet")
        self.assertIsNone(self.visible_bag.hidden_reason)

    def test_non_esani_admin_cannot_unhide_multiple(self):
        self.user = self.login("BranchAdmins")
        response = self.client.post(
            reverse("pant:qrbag_multiple_unhide"), self.post_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        # Assert: visible bag remains unchanged
        self.visible_bag.refresh_from_db()
        self.assertEqual(self.visible_bag.status, "butik_oprettet")
        self.assertIsNone(self.visible_bag.hidden_reason)
        # Assert: hidden bag without history remains unchanged
        self.hidden_bag_no_history.refresh_from_db()
        self.assertEqual(self.hidden_bag_no_history.status, "esani_skjult")
        self.assertIsNone(self.hidden_bag_no_history.hidden_reason)
        # Assert: hidden bag remains unchanged
        self.hidden_bag.refresh_from_db()
        self.assertEqual(self.hidden_bag.status, "esani_skjult")
        self.assertIsNone(self.hidden_bag.hidden_reason)
