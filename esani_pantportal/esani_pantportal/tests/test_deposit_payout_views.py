# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from esani_pantportal.models import DepositPayoutItem
from esani_pantportal.views import DepositPayoutSearchView

from .helpers import ViewTestMixin


class _BaseTestCase(ViewTestMixin, TestCase):
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
