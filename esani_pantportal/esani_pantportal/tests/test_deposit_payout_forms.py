# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date

from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase

from esani_pantportal.forms import DepositPayoutItemFilterForm
from esani_pantportal.models import Company, CompanyBranch, Kiosk


class TestDepositPayoutItemFilterForm(TestCase):
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
