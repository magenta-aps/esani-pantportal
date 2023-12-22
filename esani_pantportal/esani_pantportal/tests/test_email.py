# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailTest(TestCase):
    newsletters = True

    @classmethod
    def setUpTestData(cls) -> None:
        cls.emails = [
            "test1@example.com",
            "test2@example.com",
            "test3@example.com",
            "test4@example.com",
            "test5@example.com",
            "test6@example.com",
        ]
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.google = Company.objects.create(
            name="google",
            cvr=12312346,
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
            email=cls.emails[0],
            phone="+4542457845",
            company=cls.facebook,
            newsletter=cls.newsletters,
        )

        cls.google_admin = CompanyUser.objects.create_user(
            username="google_admin",
            password="12345",
            email=cls.emails[1],
            phone="+4542457845",
            company=cls.google,
            newsletter=cls.newsletters,
        )

        cls.facebook_branch_admin = BranchUser.objects.create_user(
            username="facebook_branch_admin",
            password="12345",
            email=cls.emails[2],
            phone="+4542457845",
            branch=cls.facebook_branch,
            newsletter=cls.newsletters,
        )

        cls.facebook_branch_user = BranchUser.objects.create_user(
            username="facebook_branch_user",
            password="12345",
            email=cls.emails[3],
            phone="+4542457845",
            branch=cls.facebook_branch,
            newsletter=cls.newsletters,
        )

        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email=cls.emails[4],
            phone="+4542457845",
            branch=cls.kiosk,
            newsletter=cls.newsletters,
        )

        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email=cls.emails[5],
            phone="+4542457845",
            newsletter=False,
        )

        call_command("create_groups")
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))
        cls.facebook_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.google_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.facebook_branch_admin.groups.add(Group.objects.get(name="BranchAdmins"))
        cls.facebook_branch_user.groups.add(Group.objects.get(name="BranchUsers"))
        cls.kiosk_admin.groups.add(Group.objects.get(name="KioskAdmins"))


class NewsEmailViewTest(EmailTest):
    def test_newsemailview(self):
        # Log in
        self.client.login(username="esani_admin", password="12345")

        # Send message.
        subject = "Your gekko's extended warranty"
        body = "13 minutes could save you 13% or more on gekko insurance"
        self.client.post(
            reverse("pant:send_newsletter"),
            {
                "subject": subject,
                "body": body,
            },
        )

        # Test that one message was sent:
        self.assertEqual(len(mail.outbox), 1)

        # Verify that everyone with newsletter=True receive
        for email_address in self.emails[0:-1]:
            self.assertIn(email_address, mail.outbox[0].to)

        # Verify that everyone with newsletter=False do NOT receive
        self.assertNotIn(self.emails[-1], mail.outbox[0].to)

        # Verify tags
        self.assertEqual(mail.outbox[0].tags, ["newsletter"])


class NoReceiversEmailViewTest(EmailTest):
    newsletters = False

    def test_newsemailview_no_receiver(self):
        # Log in
        self.client.login(username="esani_admin", password="12345")

        # Send message.
        subject = "Your gekko's extended warranty"
        body = "13 minutes could save you 13% or more on gekko insurance"
        self.client.post(
            reverse("pant:send_newsletter"),
            {
                "subject": subject,
                "body": body,
            },
        )

        # Test that one message was sent:
        self.assertEqual(len(mail.outbox), 0)
