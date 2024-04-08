# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date

from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase

from esani_pantportal.forms import DepositPayoutItemFilterForm, DepositPayoutItemForm
from esani_pantportal.models import Company, CompanyBranch, Kiosk


class BaseDepositPayoutFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company = Company.objects.create(
            name="company name",
            cvr=1111,
        )
        cls.company_branch = CompanyBranch.objects.create(
            company=cls.company,
            name="company branch name",
        )
        cls.kiosk = Kiosk.objects.create(
            name="kiosk name",
            cvr=2222,
        )


class TestDepositPayoutItemFilterForm(BaseDepositPayoutFormTest):

    def test_form_rejects_both_company_branch_and_kiosk(self):
        form = DepositPayoutItemFilterForm(
            {
                "company_branch": self.company_branch.id,
                "kiosk": self.kiosk.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            form.has_error(
                NON_FIELD_ERRORS,
                code="both_company_branch_and_kiosk_supplied",
            )
        )

    def test_form_rejects_to_date_before_from_date(self):
        form = DepositPayoutItemFilterForm(
            {
                "from_date": date(2020, 1, 1).strftime("%Y-%m-%d"),
                "to_date": date(2019, 1, 1).strftime("%Y-%m-%d"),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            form.has_error(
                NON_FIELD_ERRORS,
                code="to_date_is_before_from_date",
            )
        )


class TestDepositPayoutItemForm(BaseDepositPayoutFormTest):
    def test_choices(self):
        form = DepositPayoutItemForm()
        choices = [c[0] for c in form.fields["company_branch_or_kiosk"].choices]

        # Test that "company_branch_or_kiosk" contains both kiosks and branches
        self.assertEqual(len(choices), 3)
        self.assertIn(None, choices)
        self.assertEqual(f"company_branch-{self.company_branch.id}", choices[1])
        self.assertEqual(f"kiosk-{self.kiosk.id}", choices[2])

    def test_clean_kiosk(self):
        # Select a kiosk in the dropdown-menu
        form = DepositPayoutItemForm(
            {
                "date": date(2020, 1, 1).strftime("%Y-%m-%d"),
                "count": 1,
                "company_branch_or_kiosk": f"kiosk-{self.kiosk.id}",
                "compensation": 10,
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["kiosk"], self.kiosk)

    def test_clean_company_branch(self):
        # Select a company_branch in the dropdown-menu
        form = DepositPayoutItemForm(
            {
                "date": date(2020, 1, 1).strftime("%Y-%m-%d"),
                "count": 1,
                "company_branch_or_kiosk": f"company_branch-{self.company_branch.id}",
                "compensation": 10,
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["company_branch"], self.company_branch)
