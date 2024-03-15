# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from time import sleep
from unittest.mock import patch

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.test import TestCase
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import Product

from ..models import CompanyBranch, Kiosk, QRBag, QRStatus, User
from .conftest import LoginMixin


def mock_qr_exists(qr):
    return True


class ProductViewGuiTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prod1 = Product.objects.create(
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
        cls.prod2 = Product.objects.create(
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


class _QRBagAPITestCase(LoginMixin, ParametrizedTestCase, TestCase):
    group = None  # Overridden by subclasses

    _json_content_type = "application/json"

    def setUp(self):
        super().setUp()

        # Authenticate against Django auth
        self.user = super().login(self.group)

        # Get access token and refresh token
        self.headers = {}
        password = "12345"  # Must match password in conftest.py
        response = self._post(
            "/api/token/pair",
            username=self.user.username,
            password=password,
        )
        data = response.json()
        self.headers = {"Authorization": f"Bearer {data['access']}"}

    def _get(self, url, data=None) -> HttpResponse:
        return self.client.get(
            url,
            data=data,
            headers=self.headers,
            content_type=self._json_content_type,
        )

    def _post(self, url, **data) -> HttpResponse:
        return self.client.post(
            url,
            data,
            headers=self.headers,
            content_type=self._json_content_type,
        )

    def _get_bag(self, qr) -> HttpResponse:
        return self._get(f"/api/qrbag/{qr}")

    def _get_bag_history(self, qr) -> HttpResponse:
        return self._get(f"/api/qrbag/{qr}/history")

    def _post_bag(self, qr, **data) -> HttpResponse:
        return self._post(f"/api/qrbag/{qr}", **data)

    def _patch_bag(self, qr, **data) -> HttpResponse:
        return self.client.patch(
            f"/api/qrbag/{qr}",
            data,
            headers=self.headers,
            content_type=self._json_content_type,
        )

    def _assert_bag_dict_is(
        self,
        data: dict,
        code: str,
        active: bool,
        status: str,
        owner: str,
    ) -> None:
        self.assertEqual(data["qr"], code)
        self.assertEqual(data["active"], active)
        self.assertEqual(data["status"], status)
        self.assertEqual(data["owner"], owner)

    def _assert_bag_response_is(
        self,
        response: HttpResponse,
        code: str,
        active: bool,
        status: str,
        owner: str,
    ) -> None:
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self._assert_bag_dict_is(
            response.json(),
            code=code,
            active=active,
            status=status,
            owner=owner,
        )

    def _assert_bag_object_is(
        self,
        code: str,
        active: bool,
        status: str,
        owner: User,
    ) -> None:
        bag = QRBag.objects.get(qr=code)
        self.assertEqual(bag.qr, code)
        self.assertEqual(bag.active, active)
        self.assertEqual(bag.status, status)
        self.assertEqual(bag.owner, owner)


class QRBagTestBranchUsers(_QRBagAPITestCase):
    group = "BranchUsers"

    def test_get_404(self):
        code = "00000000005001d198"
        response = self._get_bag(code)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_create(self):
        code = "00000000005001d199"

        # Create a bag
        response = self._post_bag(
            code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
        )
        self._assert_bag_response_is(
            response,
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )

        # Retrieve the bag that was just created
        response = self._get_bag(code)
        self._assert_bag_response_is(
            response,
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )

        # Create again (should fail)
        response = self._post_bag(
            code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
        )
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_update(self):
        code = "00000000005001d200"

        # Patching a nonexistent bag creates it
        response = self._patch_bag(code, status=QRBag.STATE_VENDOR_REGISTERED)
        self._assert_bag_response_is(
            response,
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )
        self._assert_bag_object_is(
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.user_ptr,
        )

        # Update bag to active=False
        self._patch_bag(code, active=False)
        self._assert_bag_object_is(
            code=code,
            active=False,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.user_ptr,
        )
        response = self._get_bag(code)
        self._assert_bag_response_is(
            response,
            code=code,
            active=False,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_update_to_same_state_fails(self) -> None:
        # Arrange: create bag
        code = "000000000011112222"
        self._post_bag(code)
        # Act: update bag to invalid status
        response = self._patch_bag(code, status=QRBag.STATE_VENDOR_REGISTERED)
        # Assert
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)
        self.assertEqual(
            response.json()["detail"],
            f"Cannot update status to {QRBag.STATE_VENDOR_REGISTERED!r}",
        )

    @parametrize(
        "invalid_status",
        [
            (QRBag.STATE_ESANI_COLLECTED,),
            (QRBag.STATE_ESANI_REGISTERED,),
            (QRBag.STATE_ESANI_COMPENSATED,),
            ("a completely unknown status",),
        ],
    )
    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_update_to_invalid_state_fails(self, invalid_status: str) -> None:
        # Arrange: create bag
        code = "000000000011112222"
        self._post_bag(code)
        # Act: update bag to invalid status
        response = self._patch_bag(code, status=invalid_status)
        # Assert
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)
        self.assertEqual(
            response.json()["detail"], f"Invalid value {invalid_status!r} for status"
        )

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_update_to_disallowed_state_fails(self) -> None:
        # Arrange: create bag
        code = "000000000011112222"
        self._post_bag(code)
        # Act: update bag to invalid status
        response = self._patch_bag(code, status=QRBag.STATE_BACKBONE_COLLECTED)
        # Assert
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)
        self.assertEqual(
            response.json()["detail"],
            f"This user is not allowed to set status to "
            f"{QRBag.STATE_BACKBONE_COLLECTED!r}",
        )

    def test_history(self):
        code = "00000000005001d201"

        branch = self.user.branch
        company_branch = branch if isinstance(branch, CompanyBranch) else None
        kiosk = branch if isinstance(branch, Kiosk) else None

        bag = QRBag.objects.create(
            qr=code,
            active=True,
            owner=self.user,
            company_branch=company_branch,
            kiosk=kiosk,
        )

        sleep(0.1)
        bag.set_esani_collected()
        bag.save()

        sleep(0.1)
        bag.active = False
        bag.set_esani_registered()
        bag.set_esani_compensated()
        bag.save()

        response = self._get_bag_history(code)
        self.assertEqual(response.status_code, HttpResponse.status_code)
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

        self._assert_bag_dict_is(
            h1,
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )

        self._assert_bag_dict_is(
            h2,
            code=code,
            active=True,
            status=QRBag.STATE_ESANI_COLLECTED,
            owner=self.user.username,
        )

        self._assert_bag_dict_is(
            h3,
            code=code,
            active=False,
            status=QRBag.STATE_ESANI_COMPENSATED,
            owner=self.user.username,
        )

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_history_from_update(self):
        code = "00000000005001d202"

        self._post_bag(code, active=True, status=QRBag.STATE_VENDOR_REGISTERED)
        response = self._get_bag_history(code)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        data = response.json()
        self.assertEqual(data["count"], 1)
        h1 = data["items"][0]
        self._assert_bag_dict_is(
            h1,
            code=code,
            active=True,
            status=QRBag.STATE_VENDOR_REGISTERED,
            owner=self.user.username,
        )


class QRBagTestBackboneUsers(_QRBagAPITestCase):
    group = "BackboneUsers"

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_update_to_backbone_collected(self) -> None:
        # Arrange: create bag
        code = "000000000011112222"
        self._post_bag(code)
        # Act: update bag status
        response = self._patch_bag(code, status=QRBag.STATE_BACKBONE_COLLECTED)
        # Assert
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self._assert_bag_response_is(
            response,
            code=code,
            active=True,
            status=QRBag.STATE_BACKBONE_COLLECTED,
            owner=self.user.username,
        )


class QRBagTestEsaniAdmins(_QRBagAPITestCase):
    group = "EsaniAdmins"

    def test_create_disallowed(self):
        code = "00000000005001d198"
        response = self._post_bag(
            code, active=True, status=QRBag.STATE_VENDOR_REGISTERED
        )
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)


class QRBagTestKioskUsers(_QRBagAPITestCase):
    group = "KioskUsers"

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", mock_qr_exists)
    def test_create_as_kiosk_user(self):
        code = "00000000005001d19x"
        response = self._post_bag(
            code, active=True, status=QRBag.STATE_VENDOR_REGISTERED
        )
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @patch("esani_pantportal.models.QRCodeGenerator.qr_code_exists", lambda qr: False)
    def test_qr_doesnt_exist(self):
        code = "00000000005001d19x"
        response = self._post_bag(
            code, active=True, status=QRBag.STATE_VENDOR_REGISTERED
        )
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)


class QRStatusTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        QRStatus.objects.create(
            code=QRBag.STATE_VENDOR_REGISTERED,
            name_da="Oprettet af forhandler",
            name_kl="Oprettet af forhandler",
        )
        QRStatus.objects.create(
            code=QRBag.STATE_ESANI_COLLECTED,
            name_da="Modtaget af pantsystemet",
            name_kl="Modtaget af pantsystemet",
        )
        QRStatus.objects.create(
            code=QRBag.STATE_BACKBONE_COLLECTED,
            name_da="Modtaget af Backbone",
            name_kl="Modtaget af Backbone",
        )

    def test_list(self):
        response = self.client.get("/api/qrstatus/")
        self.assertEqual(
            response.json(),
            [
                {
                    "code": QRBag.STATE_VENDOR_REGISTERED,
                    "name_da": "Oprettet af forhandler",
                    "name_kl": "Oprettet af forhandler",
                },
                {
                    "code": QRBag.STATE_ESANI_COLLECTED,
                    "name_da": "Modtaget af pantsystemet",
                    "name_kl": "Modtaget af pantsystemet",
                },
                {
                    "code": QRBag.STATE_BACKBONE_COLLECTED,
                    "name_da": "Modtaget af Backbone",
                    "name_kl": "Modtaget af Backbone",
                },
            ],
        )
