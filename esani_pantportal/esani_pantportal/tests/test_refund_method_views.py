# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.forms import RefundMethodRegisterForm
from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
    RefundMethod,
)

from .conftest import LoginMixin


class BaseRefundMethodTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.brugseni = Company.objects.create(
            name="brugseni",
            cvr=12312346,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
        )
        cls.brugseni_nuuk = CompanyBranch.objects.create(
            company=cls.brugseni,
            name="brugseni Nuuk",
            address="food",
            postal_code="12311",
            city="Nuuk",
            phone="+4542457845",
            location_id=2,
        )
        cls.brugseni_sisimiut = CompanyBranch.objects.create(
            company=cls.brugseni,
            name="brugseni Sisimiut",
            address="food",
            postal_code="12311",
            city="Sisimiut",
            phone="+4542457845",
            location_id=3,
        )
        cls.kiosk = Kiosk.objects.create(
            name="Nuuk kiosk",
            address="food",
            postal_code="12311",
            city="Nuuk",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
        )
        cls.brugseni_admin = CompanyUser.objects.create_user(
            username="brugseni_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.brugseni,
        )
        cls.brugseni_nuuk_admin = BranchUser.objects.create_user(
            username="brugseni_nuuk_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.brugseni_nuuk,
        )
        cls.brugseni_nuuk_user = BranchUser.objects.create_user(
            username="brugseni_nuuk_user",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.brugseni_nuuk,
        )
        cls.brugseni_sisimiut_admin = BranchUser.objects.create_user(
            username="brugseni_sisimiut_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.brugseni_sisimiut,
        )
        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.kiosk,
        )
        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
        )

        call_command("create_groups")
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))
        cls.brugseni_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.brugseni_nuuk_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.brugseni_nuuk_user.groups.add(Group.objects.get(name="CompanyUsers"))
        cls.brugseni_sisimiut_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.kiosk_admin.groups.add(Group.objects.get(name="KioskAdmins"))

        # Brugseni Nuuk has a refund machine with a safety container
        cls.brugseni_nuuk_refund_method = RefundMethod.objects.create(
            compensation=100,
            serial_number="123",
            branch=cls.brugseni_nuuk,
        )

        # Brugseni Sisimiut has a refund machine with a crusher
        cls.brugseni_sisimiut_refund_method = RefundMethod.objects.create(
            compensation=200,
            serial_number="123",
            branch=cls.brugseni_sisimiut,
        )

        # The local kiosk sorts manually
        cls.kiosk_refund_method = RefundMethod.objects.create(
            compensation=300,
            serial_number="",
            kiosk=cls.kiosk,
        )

    @staticmethod
    def make_form_data(form):
        form_data = {}
        for field_name, field in form.fields.items():
            form_data[field_name] = form.get_initial_for_field(field, field_name)

        return form_data


class RefundMethodListTest(BaseRefundMethodTest):
    def test_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]
        self.assertIn(self.kiosk_refund_method.id, ids)
        self.assertIn(self.brugseni_sisimiut_refund_method.id, ids)
        self.assertIn(self.brugseni_nuuk_refund_method.id, ids)
        self.assertEqual(len(ids), 3)

    def test_esani_admin_filtered_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:refund_method_list") + "?branch__name=Nuuk"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]
        self.assertIn(self.kiosk_refund_method.id, ids)
        self.assertIn(self.brugseni_nuuk_refund_method.id, ids)
        self.assertEqual(len(ids), 2)

    def test_brugseni_admin_view(self):
        self.client.login(username="brugseni_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]
        self.assertIn(self.brugseni_sisimiut_refund_method.id, ids)
        self.assertIn(self.brugseni_nuuk_refund_method.id, ids)
        self.assertEqual(len(ids), 2)

    def test_brugseni_nuuk_admin_view(self):
        self.client.login(username="brugseni_nuuk_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]
        self.assertIn(self.brugseni_nuuk_refund_method.id, ids)
        self.assertEqual(len(ids), 1)

    def test_brugseni_nuuk_user_view(self):
        self.client.login(username="brugseni_nuuk_user", password="12345")
        response = self.client.get(reverse("pant:refund_method_list"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_kiosk_admin_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]
        self.assertIn(self.kiosk_refund_method.id, ids)
        self.assertEqual(len(ids), 1)


class CreateRefundMethodViewTest(BaseRefundMethodTest):
    def test_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_register"))
        form = response.context["form"]

        # Note that "None" is also a choice
        self.assertEqual(len(form.fields["branch"].choices), 3)
        self.assertEqual(len(form.fields["kiosk"].choices), 2)

    def test_brugseni_admin_view(self):
        self.client.login(username="brugseni_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_register"))
        form = response.context["form"]

        # The Brugseni admin can choose all Brugseni refund machines
        # "None" is not an option for him
        self.assertEqual(len(form.fields["branch"].choices), 2)
        self.assertEqual(len(form.fields["kiosk"].choices), 0)

        branch_ids = [option[0] for option in form.fields["branch"].choices]

        self.assertIn(self.brugseni_nuuk.id, branch_ids)
        self.assertIn(self.brugseni_sisimiut.id, branch_ids)

    def test_brugseni_nuuk_admin_view(self):
        self.client.login(username="brugseni_nuuk_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_register"))
        form = response.context["form"]

        # The Brugseni admin in Nuuk can only create refund machines at his own branch.
        # "None" is not an option for him
        self.assertEqual(len(form.fields["branch"].choices), 1)
        self.assertEqual(len(form.fields["kiosk"].choices), 0)
        self.assertEqual(self.brugseni_nuuk.id, form.fields["branch"].choices[0][0])

        # He does not need to be able to change this field, as there is only one branch
        # to choose from
        self.assertTrue(form.fields["branch"].disabled)

    def test_kiosk_admin_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        response = self.client.get(reverse("pant:refund_method_register"))
        form = response.context["form"]

        # The kiosk admincan only create refund machines at his own kiosk.
        # "None" is not an option for him
        self.assertEqual(len(form.fields["branch"].choices), 0)
        self.assertEqual(len(form.fields["kiosk"].choices), 1)
        self.assertEqual(self.kiosk.id, form.fields["kiosk"].choices[0][0])

        # He does not need to be able to change this field, as there is only one kiosk
        # to choose from
        self.assertTrue(form.fields["kiosk"].disabled)


class CreateRefundMethodFormTest(BaseRefundMethodTest):
    def make_dummy_data(
        self,
        compensation=200,
        serial_number="666",
        branch=None,
        kiosk=None,
    ):
        data = {
            "compensation": compensation,
            "serial_number": serial_number,
            "kiosk": kiosk.pk if kiosk else None,
            "branch": branch.pk if branch else None,
        }
        if not kiosk:
            del data["kiosk"]
        if not branch:
            del data["branch"]
        return data

    def test_form(self):
        data = self.make_dummy_data(branch=self.brugseni_nuuk)
        form = RefundMethodRegisterForm(data)
        self.assertTrue(form.is_valid())

    def test_post(self):
        self.client.login(username="esani_admin", password="12345")
        data = self.make_dummy_data(branch=self.brugseni_nuuk)

        qs = RefundMethod.objects.filter(serial_number=data["serial_number"])
        self.assertFalse(qs.exists())
        response = self.client.post(
            reverse("pant:refund_method_register"), data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "esani_pantportal/refund_method/list.html")
        self.assertTrue(qs.exists())

    def test_form_no_branch_or_kiosk(self):
        # A refund machine must belong to either a kiosk or a branch.
        data = self.make_dummy_data(branch=None, kiosk=None)
        form = RefundMethodRegisterForm(data)
        self.assertFalse(form.is_valid())

    def test_form_branch_and_kiosk(self):
        # A refund machine cannot be at a branch AND at a kiosk. The user must choose.
        data = self.make_dummy_data(branch=self.brugseni_nuuk, kiosk=self.kiosk)
        form = RefundMethodRegisterForm(data)
        self.assertFalse(form.is_valid())

    def test_form_serial_number_not_supplied(self):
        data = self.make_dummy_data(
            branch=self.brugseni_nuuk,
            serial_number="",
        )

        form = RefundMethodRegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("serial_number", form.errors)


class DeleteRefundMethodTest(BaseRefundMethodTest):
    def delete_refund_method(self, pk):
        kwargs = {"pk": pk}
        return self.client.post(reverse("pant:refund_method_delete", kwargs=kwargs))

    def test_esani_admin_response(self):
        self.client.login(username="esani_admin", password="12345")

        pk_to_delete = self.brugseni_nuuk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(RefundMethod.objects.filter(pk=pk_to_delete).exists())

    def test_brugseni_admin_response(self):
        self.client.login(username="brugseni_admin", password="12345")
        pk_to_delete = self.brugseni_nuuk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(RefundMethod.objects.filter(pk=pk_to_delete).exists())

        # A brugseni admin should not be allowed to delete a kiosk refund machine
        pk_to_delete = self.kiosk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_brugseni_nuuk_admin_response(self):
        self.client.login(username="brugseni_nuuk_admin", password="12345")
        pk_to_delete = self.brugseni_nuuk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(RefundMethod.objects.filter(pk=pk_to_delete).exists())

        # A Nuuk admin should not be allowed to delete a Sisimiut machine
        pk_to_delete = self.brugseni_sisimiut_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_kiosk_admin_response(self):
        self.client.login(username="kiosk_admin", password="12345")

        pk_to_delete = self.kiosk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(RefundMethod.objects.filter(pk=pk_to_delete).exists())

        # A kiosk admin should not be able to delete brugseni machines
        pk_to_delete = self.brugseni_nuuk_refund_method.pk
        response = self.delete_refund_method(pk_to_delete)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
