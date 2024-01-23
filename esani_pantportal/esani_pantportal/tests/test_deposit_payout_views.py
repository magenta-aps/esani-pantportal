# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from esani_pantportal.models import (
    Company,
    CompanyBranch,
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    Kiosk,
    Product,
)
from esani_pantportal.views import DepositPayoutSearchView

from .conftest import LoginMixin


class TestDepositPayoutSearchView(LoginMixin, TestCase):
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

        cls.deposit_payout = DepositPayout.objects.create(
            filename="foo.csv",
            from_date=datetime.date(2024, 1, 1),
            to_date=datetime.date(2024, 2, 1),
            item_count=0,
        )

        shared = {
            "product": cls.product,
            "location_id": 123,
            "rvm_serial": 123,
            "date": datetime.date(2024, 1, 28),
            "barcode": "barcode",
            "count": 42,
        }

        cls.deposit_payout_item_1 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            company_branch=cls.company_branch,
            **shared,
        )

        cls.deposit_payout_item_2 = DepositPayoutItem.objects.create(
            deposit_payout=cls.deposit_payout,
            kiosk=cls.kiosk,
            **shared,
        )

    def _login(self):
        self.client.login(username="esani_admin", password="12345")

    def _get_response(self, **query_params):
        self._login()
        return self.client.get(
            reverse("pant:deposit_payout_list")
            + (f"?{urlencode(query_params)}" if query_params else "")
        )

    def _assert_list_contents(self, response, values, count):
        self.assertQuerySetEqual(
            response.context["items"],
            values,
            transform=lambda obj: obj.company_branch or obj.kiosk,
            ordered=False,
        )
        self.assertEqual(response.context["page_obj"].paginator.count, count)

    def _assert_page_parameters(
        self,
        response,
        size=DepositPayoutSearchView.paginate_by,
        page=1,
        sort="",
        order="",
    ):
        self.assertEqual(response.context["page_size"], size)
        self.assertEqual(response.context["page_number"], page)
        self.assertEqual(response.context["sort_name"], sort)
        self.assertEqual(response.context["sort_order"], order)

    def test_esani_admin_can_access_view(self):
        response = self._get_response()
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_filters(self):
        # Test without filters
        response = self._get_response()
        self._assert_list_contents(
            response,
            [self.company_branch, self.kiosk],
            DepositPayoutItem.objects.count(),
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

    def test_sorting(self):
        # Sort items on "source" in reverse order
        response = self._get_response(sort="source", order="desc")
        self.assertQuerySetEqual(
            response.context["items"],
            [self.kiosk.name, self.company_branch.name],
            transform=lambda obj: (
                obj.company_branch.name if obj.company_branch else obj.kiosk.name
            ),
            ordered=True,
        )

    def test_page_size(self):
        # Use a page size of 1 to enforce pagination of the two items
        response = self._get_response(size=1)
        self._assert_page_parameters(response, size=1)
        self.assertEqual(
            response.context["page_obj"].paginator.count,
            DepositPayoutItem.objects.count(),
        )
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

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
                ]
            },
        )
        # Assert that we "processed" only two items
        self.assertDictEqual(response.json(), {"all": False, "count": 2})

    def test_post_selection_all(self):
        self._login()
        # Post "selection=all"
        response = self.client.post(
            reverse("pant:deposit_payout_list"),
            data={"selection": "all"},
        )
        # Assert that we "processed" all (2) deposit payout items
        self.assertDictEqual(response.json(), {"all": True, "count": 2})
