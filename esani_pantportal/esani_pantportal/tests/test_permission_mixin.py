from unittest.mock import MagicMock

from django.test import TestCase

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
)
from esani_pantportal.view_mixins import PermissionRequiredMixin


class PermissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
        )

        cls.facebook_admin = CompanyUser.objects.create_user(
            username="facebook_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.facebook,
        )

        cls.facebook_branch_admin = BranchUser.objects.create_user(
            username="facebook_branch_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.facebook_branch,
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

    def setUp(self):
        self.mixin = PermissionRequiredMixin()
        self.mixin.request = MagicMock()
        self.mixin.request.user = MagicMock()

    def test_permissions_ok(self):
        self.mixin.request.user.get_all_permissions.return_value = [
            "view_me",
            "change_me",
        ]

        self.mixin.required_permissions = ["delete_me"]
        self.assertFalse(self.mixin.permissions_ok)

        self.mixin.required_permissions = ["view_me"]
        self.assertTrue(self.mixin.permissions_ok)

    def test_groups_ok(self):
        admin_group = MagicMock()
        admin_group.name = "admin_group"
        self.mixin.request.user.groups.all.return_value = [admin_group]

        self.mixin.required_groups = ["admin_group"]
        self.assertTrue(self.mixin.groups_ok)

        self.mixin.required_groups = ["super_admin_group"]
        self.assertFalse(self.mixin.groups_ok)

    def test_user_type_ok(self):
        self.mixin.request.user.user_type = 1
        self.mixin.allowed_user_types = [2]
        self.assertFalse(self.mixin.user_type_ok)

        self.mixin.allowed_user_types = [1]
        self.assertTrue(self.mixin.user_type_ok)

    def test_has_superuser_permissions(self):
        self.mixin.request.user.is_superuser = True
        self.assertTrue(self.mixin.has_permissions)

    def test_users_in_same_company(self):
        # Branch admins are in the same company as others in the same branch.
        self.mixin.request.user = self.facebook_branch_admin
        self.assertEqual(
            self.mixin.users_in_same_company, [self.facebook_branch_admin.id]
        )

        # Company admins are considered in the same company as other company users
        # in their company as well as branch users in branches belonging to their
        # company
        self.mixin.request.user = self.facebook_admin
        self.assertEqual(
            self.mixin.users_in_same_company,
            [self.facebook_admin.id, self.facebook_branch_admin.id],
        )

        # Kiosk admins are in the same company as other users working in their kiosk
        self.mixin.request.user = self.kiosk_admin
        self.assertEqual(self.mixin.users_in_same_company, [self.kiosk_admin.id])

        # ESANI admins do not have a company so an empty list is returned.
        self.mixin.request.user = self.esani_admin
        self.assertEqual(self.mixin.users_in_same_company, [])
