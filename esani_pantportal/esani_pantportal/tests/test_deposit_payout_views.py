# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import uuid
from csv import DictReader
from http import HTTPStatus
from io import StringIO

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from esani_pantportal.models import (
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    Kiosk,
    Product,
    QRBag,
)
from esani_pantportal.views import DepositPayoutSearchView

from .conftest import LoginMixin


class _BaseTestCase(LoginMixin, TestCase):
    url = None

    @classmethod
    def setUpTestData(cls) -> None:
        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@example.org",
            phone="+4500000000",
        )
        call_command("create_groups")
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))

        cls.product = Product.objects.create(
            product_name="product_name",
            barcode="barcode",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            danish="J",
        )

        shared = {
            "address": "foo",
            "postal_code": "123",
            "city": "test city",
            "phone": "+4500000000",
        }

        cls.company = Company.objects.create(
            name="company",
            cvr=12345678,
            **shared,
        )

        cls.company_branch = CompanyBranch.objects.create(
            company=cls.company,
            name="company branch",
            location_id=123,
            **shared,
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            location_id=456,
            cvr=12345678,
            **shared,
        )

        cls.qr_bag = QRBag.objects.create(
            company_branch=cls.company_branch,
            qr="1234",
            status="esani_optalt",
        )

        cls.deposit_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_API,
            source_identifier="unused",
            from_date=datetime.date(2024, 1, 1),
            to_date=datetime.date(2024, 2, 1),
            item_count=0,
        )

        shared = {
            "product": cls.product,
            "location_id": 123,
            "rvm_serial": 123,
            "barcode": "barcode",
            "count": 42,
        }

        cls.deposit_payout_item_1 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            company_branch=cls.company_branch,
            date=datetime.date(2024, 1, 28),
            qr_bag=cls.qr_bag,
            **shared,
        )

        cls.deposit_payout_item_2 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            kiosk=cls.kiosk,
            date=datetime.date(2024, 1, 29),
            **shared,
        )

        cls.deposit_payout_item_3 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            kiosk=cls.kiosk,
            date=datetime.date(2024, 1, 29),
            file_id=uuid.uuid4(),
            **shared,
        )

    def _login(self):
        self.client.login(username="esani_admin", password="12345")

    def _get_url(self, **query_params):
        return reverse(self.url) + (
            f"?{urlencode(query_params)}" if query_params else ""
        )

    def _get_response(self, **query_params):
        self._login()
        return self.client.get(self._get_url(**query_params))

    def _assert_list_contents(
        self,
        response,
        values,
        count,
        already_exported=None,
    ):
        items = response.context["items"]
        self.assertEqual(
            sorted([item["source"].split(" - ")[0] for item in items]),
            sorted([v.name for v in values]),
        )
        self.assertListEqual(
            [item["already_exported"] for item in items],
            [_("Nej")] * len(values) if already_exported is None else already_exported,
        )
        self.assertEqual(response.context["total"], count)

    def _assert_page_parameters(
        self,
        response,
        size=DepositPayoutSearchView.paginate_by,
        page=1,
        sort="",
        order="",
    ):
        search_data = response.context["search_data"]
        self.assertEqual(search_data.get("limit"), size)
        self.assertEqual(search_data.get("page_number"), page)
        self.assertEqual(search_data.get("sort", ""), sort)
        self.assertEqual(search_data.get("order", ""), order)

    def _assert_csv_response(self, response, expected_length=None):
        csv_rows = list(
            DictReader(StringIO(response.content.decode("utf-8")), delimiter=";")
        )
        self.assertEqual(len(csv_rows), expected_length)

    def _assert_response_is_redirect_with_message(self, response, message):
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertEqual(
            str(list(get_messages(response.wsgi_request))[0]),
            message,
        )


class TestDepositPayoutSearchView(_BaseTestCase):
    url = "pant:deposit_payout_list"

    def test_esani_admin_can_access_view(self):
        response = self._get_response()
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_filters(self):
        # Test without filters
        response = self._get_response()
        self._assert_list_contents(
            response,
            [self.company_branch, self.kiosk],
            # `self.deposit_payout_item_3` is not displayed by default, as it has a
            # `file_id` and thus is considered already exported.
            2,
        )
        self._assert_page_parameters(response)

        # Test filtering on company branch
        response = self._get_response(company_branch=self.company_branch.pk)
        self._assert_list_contents(response, [self.company_branch], 1)
        self._assert_page_parameters(response)

        # Test filtering on kiosk
        response = self._get_response(kiosk=self.kiosk.pk)
        self._assert_list_contents(response, [self.kiosk], 1)
        self._assert_page_parameters(response)

        # Test filtering on `from_date`
        response = self._get_response(
            from_date=datetime.date(2024, 1, 29).strftime("%Y-%m-%d"),
        )
        # Only the 'kiosk' deposit payout item matches (the other is on Jan 28.)
        self._assert_list_contents(response, [self.kiosk], 1)
        self._assert_page_parameters(response)

        # Test filtering on `to_date`
        response = self._get_response(
            to_date=datetime.date(2024, 1, 28).strftime("%Y-%m-%d"),
        )
        # Only the 'company branch' deposit payout item matches (the other is on
        # Jan 29.)
        self._assert_list_contents(response, [self.company_branch], 1)
        self._assert_page_parameters(response)

        # Test filtering on `already_exported`
        response = self._get_response(already_exported="on")
        # All three items are included when `already_exported` is True
        self._assert_list_contents(
            response,
            [self.company_branch, self.kiosk, self.kiosk],
            3,
            already_exported=[_("Ja"), _("Nej"), _("Nej")],
        )

    def test_sorting(self):
        # Sort items on "source" in reverse order
        response = self._get_response(sort="source", order="desc")
        items = response.context["items"]

        self.assertIn(self.kiosk.name, items[0]["source"])
        self.assertIn(self.company_branch.name, items[1]["source"])

        response = self._get_response(sort="source", order="asc")
        items = response.context["items"]

        self.assertIn(self.company_branch.name, items[0]["source"])
        self.assertIn(self.kiosk.name, items[1]["source"])

    def test_page_size(self):
        # Use a page size of 1 to enforce pagination of the two items
        response = self._get_response(limit=1)
        self._assert_page_parameters(response, size=1)
        self.assertEqual(
            response.context["total"],
            # `self.deposit_payout_item_3` is not displayed by default, as it has a
            # `file_id` and thus is considered already exported.
            2,
        )
        self.assertEqual(len(response.context["items"]), 1)
        self.assertEqual(response.context["total"], 2)

    def test_post_ids(self):
        self._login()
        # Post the IDs of the two deposit payout items, plus an unknown ID
        response = self.client.post(
            reverse("pant:deposit_payout_list"),
            data={
                "id": [
                    self.deposit_payout_item_1.pk,
                    self.deposit_payout_item_2.pk,
                    42,
                    "1.234",
                ]
            },
        )
        # Assert that we receive the expected CSV response
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=4)

    def test_post_selection_all_dry(self):
        self._login()
        # Post "selection=all"
        response = self.client.post(
            reverse("pant:deposit_payout_list"),
            data={"selection": "all-dry"},
        )
        # Assert that we receive the expected CSV response
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=4)

    def test_post_selection_all_dry_with_filters(self):
        self._login()

        # When filtering for to_date=2024-01-28 we filter out deposit_payout_item_2
        response = self.client.post(
            self._get_url(to_date="2024-01-28"),
            data={"selection": "all-dry"},
        )
        # Assert that we receive the expected CSV response
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=2)

    def test_post_selection_all_wet_with_filters(self):
        self._login()

        # When filtering for to_date=2024-01-28 we filter out deposit_payout_item_2
        response = self.client.post(
            self._get_url(to_date="2024-01-28"),
            data={"selection": "all-wet"},
        )

        # Assert that we receive the expected CSV response
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=2)

        # Assert that the underlying deposit payout item is marked as exported
        self.deposit_payout_item_1.refresh_from_db()
        self.assertIsNotNone(self.deposit_payout_item_1.file_id)

        # Assert that the underlying deposit payout item is *not* marked as exported
        # (it does not match the filter on `to_date` above.)
        self.deposit_payout_item_2.refresh_from_db()
        self.assertIsNone(self.deposit_payout_item_2.file_id)

        # Assert that the underlying QR bag object is updated
        self.qr_bag.refresh_from_db()
        self.assertEqual(self.qr_bag.status, "esani_udbetalt")

    def test_post_selection_all_dry_with_hidden_items(self):
        self._login()

        # When limit=1, some items are on the next page. We still expect them in the
        # exported csv-file
        response = self.client.post(
            self._get_url(limit=1),
            data={"selection": "all-dry"},
        )
        # Assert that we receive the expected CSV response
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=4)

    def test_post_handles_empty_queryset(self):
        expected_message = _("Ingen linjer er valgt")

        self._login()

        # Test 1: POST invalid item IDs, resulting in an empty queryset
        response = self.client.post(self._get_url(), data={"id": "-1"})
        self._assert_response_is_redirect_with_message(response, expected_message)

        # Test 2: POST invalid filter data, resulting in an invalid form
        response = self.client.post(
            self._get_url(from_date="99"),
            data={"selection": "all"},
        )
        self._assert_response_is_redirect_with_message(response, expected_message)

    def test_invalid_filters_returns_empty_queryset(self):
        self._login()
        # Supply invalid filter parameters
        response = self._get_response(
            from_date=datetime.date(2020, 1, 1).strftime("%Y-%m-%d"),
            to_date=datetime.date(2019, 1, 1).strftime("%Y-%m-%d"),
        )
        self.assertNotIn("items", response.context)
        self.assertEquals(
            ["Angiv venligst en fra-dato, der ligger før til-datoen."],
            response.context["form"].errors["__all__"],
        )


class TestDepositPayoutSearchViewMissingData(_BaseTestCase):
    url = "pant:deposit_payout_list"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        shared = {
            "location_id": 123,
            "rvm_serial": 123,
            "barcode": "barcode",
            "count": 42,
        }

        # Deposit item with neither a company or kiosk
        cls.deposit_payout_item_3 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            date=datetime.date(2024, 1, 29),
            product=cls.product,
            **shared,
        )

        # Deposit item without a product
        cls.deposit_payout_item_4 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            date=datetime.date(2024, 1, 29),
            kiosk=cls.kiosk,
            **shared,
        )

    def test_missing_company(self):
        response = self._get_response()

        items = {d["id"]: d for d in response.context["items"]}
        item3 = items[self.deposit_payout_item_3.id]

        self.assertIn("Ingen matchende kæde eller butik", item3["source"])

    def test_missing_product(self):
        response = self._get_response()

        items = {d["id"]: d for d in response.context["items"]}
        item4 = items[self.deposit_payout_item_4.id]

        self.assertIn("Intet matchende produkt", item4["product"])


class TestDepositPayoutArchiveView(_BaseTestCase):
    url = "pant:deposit_payout_archive"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        # Arrange: give deposit payout items 1 and 2 (the same) `file_id`
        cls.file_id = uuid.uuid4()
        DepositPayoutItem.objects.filter(
            id__in=[
                cls.deposit_payout_item_1.id,
                cls.deposit_payout_item_2.id,
            ]
        ).update(file_id=cls.file_id)

    def test_get_displays_single_archive_item(self):
        # Act
        response = self._get_response()
        # Assert: page contains two items:
        # - deposit payout items 1 and 3 are grouped by the same file ID.
        # - deposit payout item 3 has its own file ID (and therefore its own group.)
        items = response.context["items"]
        self.assertEqual(len(items), 2)
        # Assert: check attributes of the group belonging to `self.file_id`, i.e. the
        # group consisting of deposit payout items 1 and 2.
        group = [it for it in items if it["file_id"] == self.file_id][0]
        self.assertEqual(group["file_id"], self.file_id)
        self.assertEqual(group["from_date"], self.deposit_payout_item_1.date)
        self.assertEqual(group["to_date"], self.deposit_payout_item_2.date)
        self.assertEqual(group["count"], 2)
        self.assertIn(
            f'<a href="?file_id={self.file_id}" ',
            group["actions"],
        )

    def test_get_valid_file_id_returns_csv(self):
        # Act
        response = self._get_response(file_id=self.file_id)
        # Assert
        self.assertEqual(response["Content-Type"], "text/csv")
        self._assert_csv_response(response, expected_length=4)

    def test_get_invalid_file_id_displays_message(self):
        # Act
        response = self._get_response(file_id=uuid.uuid4())
        # Assert
        self._assert_response_is_redirect_with_message(
            response,
            _("Ingen linjer fundet for det angivne fil-ID"),
        )
