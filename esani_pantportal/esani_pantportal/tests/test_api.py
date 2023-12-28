# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import json
from time import sleep

from django.test import TestCase

from esani_pantportal.models import Product

from ..models import CompanyBranch, Kiosk, QRBag
from .conftest import LoginMixin


class ProductViewGuiTest(LoginMixin, TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="00101122",
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
        self.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="00020002",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    def test_get_products(self):
        response = self.client.get("/api/produkter")
        output = response.json()

        self.assertEqual(output["count"], 1)
        self.assertEqual(output["items"][0]["product_name"], self.prod1.product_name)
        self.assertEqual(output["items"][0]["barcode"], self.prod1.barcode)


class QRBagTest(LoginMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self) -> None:
        super().setUp()
        self.user = self.login("BranchUsers")

    def login(self, group="EsaniAdmins"):
        user = super().login(group)
        password = "12345"  # Must match password in conftest.py
        response = self.client.post(
            "/api/token/pair",
            {"username": user.username, "password": password},
            content_type="application/json",
        )
        data = response.json()
        self.accesstoken = data["access"]
        self.refreshtoken = data["refresh"]
        self.headers = {
            "Authorization": f"Bearer {self.accesstoken}",
            "Content-Type": "application/json",
        }
        return user

    def test_get_404(self):
        code = "00000000005001d198"
        response = self.client.get(f"/api/qrbag/{code}", headers=self.headers)
        self.assertEqual(response.status_code, 404, response.content)

    def test_create_disallowed(self):
        self.user = self.login("EsaniAdmins")
        code = "00000000005001d198"
        response = self.client.post(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": True, "status": "oprettet"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_create(self):
        code = "00000000005001d199"
        response = self.client.post(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": True, "status": "oprettet"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["qr"], "00000000005001d199")
        self.assertEqual(data["active"], True)
        self.assertEqual(data["status"], "oprettet")
        self.assertEqual(data["owner"], self.user.username)

        response = self.client.get(f"/api/qrbag/{code}", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["qr"], "00000000005001d199")
        self.assertEqual(data["active"], True)
        self.assertEqual(data["status"], "oprettet")
        self.assertEqual(data["owner"], self.user.username)

        response = self.client.post(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": True, "status": "oprettet"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_update(self):
        code = "00000000005001d200"
        response = self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"status": "oprettet"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        item = QRBag.objects.get(qr=code)
        self.assertEqual(data["qr"], code)
        self.assertEqual(data["active"], True)
        self.assertEqual(data["status"], "oprettet")
        self.assertEqual(data["owner"], self.user.username)
        self.assertEqual(item.qr, code)
        self.assertEqual(item.active, True)
        self.assertEqual(item.status, "oprettet")
        self.assertEqual(item.owner, self.user.user_ptr)

        response = self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"status": "i brug"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        item.refresh_from_db()
        self.assertEqual(data["qr"], code)
        self.assertEqual(data["active"], True)
        self.assertEqual(data["status"], "i brug")
        self.assertEqual(item.qr, code)
        self.assertEqual(item.active, True)
        self.assertEqual(item.status, "i brug")
        self.assertEqual(item.owner, self.user.user_ptr)

        self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": False}),
            content_type="application/json",
            headers=self.headers,
        )
        response = self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"status": "afsluttet"}),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        item.refresh_from_db()
        self.assertEqual(data["qr"], code)
        self.assertEqual(data["active"], False)
        self.assertEqual(data["status"], "afsluttet")
        self.assertEqual(data["owner"], self.user.username)
        self.assertEqual(item.qr, code)
        self.assertEqual(item.active, False)
        self.assertEqual(item.status, "afsluttet")
        self.assertEqual(item.owner, self.user.user_ptr)

        response = self.client.get(f"/api/qrbag/{code}", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        item.refresh_from_db()
        self.assertEqual(data["qr"], code)
        self.assertEqual(data["active"], False)
        self.assertEqual(data["status"], "afsluttet")
        self.assertEqual(data["owner"], self.user.username)
        self.assertEqual(item.qr, code)
        self.assertEqual(item.active, False)
        self.assertEqual(item.status, "afsluttet")
        self.assertEqual(item.owner, self.user.user_ptr)

    def test_history(self):
        code = "00000000005001d201"

        branch = self.user.branch
        companybranch = branch if isinstance(branch, CompanyBranch) else None
        kiosk = branch if isinstance(branch, Kiosk) else None

        bag = QRBag.objects.create(
            qr=code,
            active=True,
            status="oprettet",
            owner=self.user,
            companybranch=companybranch,
            kiosk=kiosk,
        )

        sleep(0.1)
        bag.status = "under transport"
        bag.save()

        sleep(0.1)
        bag.active = False
        bag.status = "afsluttet"
        bag.save()

        response = self.client.get(f"/api/qrbag/{code}/history", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["count"], 3)
        h1 = data["items"][0]
        h2 = data["items"][1]
        h3 = data["items"][2]
        self.assertTrue(
            h1["updated"] < h2["updated"], f'{h1["updated"]} < {h2["updated"]}'
        )
        self.assertTrue(
            h1["history_date"] < h2["history_date"],
            f'{h1["history_date"]} < {h2["history_date"]}',
        )
        self.assertTrue(
            h2["updated"] < h3["updated"], f'{h2["updated"]} < {h3["updated"]}'
        )
        self.assertTrue(
            h2["history_date"] < h3["history_date"],
            f'{h2["history_date"]} < {h3["history_date"]}',
        )

        self.assertEqual(h1["qr"], code)
        self.assertEqual(h1["active"], True)
        self.assertEqual(h1["status"], "oprettet")
        self.assertEqual(h1["owner"], self.user.username)

        self.assertEqual(h2["qr"], code)
        self.assertEqual(h2["active"], True)
        self.assertEqual(h2["status"], "under transport")
        self.assertEqual(h2["owner"], self.user.username)

        self.assertEqual(h3["qr"], code)
        self.assertEqual(h3["active"], False)
        self.assertEqual(h3["status"], "afsluttet")
        self.assertEqual(h3["owner"], self.user.username)

    def test_history_from_update(self):
        code = "00000000005001d202"
        self.client.post(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": True, "status": "oprettet"}),
            content_type="application/json",
            headers=self.headers,
        )
        sleep(0.1)
        self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": True, "status": "under transport"}),
            content_type="application/json",
            headers=self.headers,
        )
        sleep(0.1)
        self.client.patch(
            f"/api/qrbag/{code}",
            data=json.dumps({"active": False, "status": "afsluttet"}),
            content_type="application/json",
            headers=self.headers,
        )
        response = self.client.get(f"/api/qrbag/{code}/history", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["count"], 3)
        h1 = data["items"][0]
        h2 = data["items"][1]
        h3 = data["items"][2]
        self.assertTrue(
            h1["updated"] < h2["updated"], f'{h1["updated"]} < {h2["updated"]}'
        )
        self.assertTrue(
            h1["history_date"] < h2["history_date"],
            f'{h1["history_date"]} < {h2["history_date"]}',
        )
        self.assertTrue(
            h2["updated"] < h3["updated"], f'{h2["updated"]} < {h3["updated"]}'
        )
        self.assertTrue(
            h2["history_date"] < h3["history_date"],
            f'{h2["history_date"]} < {h3["history_date"]}',
        )

        self.assertEqual(h1["qr"], code)
        self.assertEqual(h1["active"], True)
        self.assertEqual(h1["status"], "oprettet")
        self.assertEqual(h1["owner"], self.user.username)

        self.assertEqual(h2["qr"], code)
        self.assertEqual(h2["active"], True)
        self.assertEqual(h2["status"], "under transport")
        self.assertEqual(h2["owner"], self.user.username)

        self.assertEqual(h3["qr"], code)
        self.assertEqual(h3["active"], False)
        self.assertEqual(h3["status"], "afsluttet")
        self.assertEqual(h3["owner"], self.user.username)
