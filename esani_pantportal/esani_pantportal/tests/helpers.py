# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import datetime
import uuid
from csv import DictReader
from io import StringIO

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
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
    QRBag,
)

from .conftest import LoginMixin


class ViewTestMixin(LoginMixin):
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
        )
        cls.qr_bag.set_esani_collected()
        cls.qr_bag.set_esani_registered()
        cls.qr_bag.save()

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
