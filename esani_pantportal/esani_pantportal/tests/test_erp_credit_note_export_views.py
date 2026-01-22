# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import uuid
from datetime import date

from django.http import HttpResponseNotFound
from django.templatetags.l10n import localize
from django.test import TestCase
from django.utils.translation import gettext as _

from esani_pantportal.models import DepositPayoutItem, ERPCreditNoteExport

from .helpers import ViewTestMixin


class TestERPCreditNoteExportSearchView(ViewTestMixin, TestCase):
    maxDiff = None

    url = "pant:erp_credit_note_export_list"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        # Add ERP credit note export objects
        shared = {
            "from_date": date(2023, 1, 1),
            "to_date": date(2023, 1, 31),
        }
        cls.file_id_1 = uuid.uuid4()
        cls.erp_export_1 = ERPCreditNoteExport.objects.create(
            file_id=cls.file_id_1,
            **shared,
        )
        cls.file_id_2 = uuid.uuid4()
        cls.erp_export_2 = ERPCreditNoteExport.objects.create(
            file_id=cls.file_id_2,
            **shared,
        )

        # Mark deposit payout items as belonging to export 1
        DepositPayoutItem.objects.update(file_id=cls.file_id_1)

    def test_get_displays_expected_items(self):
        # Act
        response = self._get_response()
        # Assert
        self.assertListEqual(
            response.context["items"],
            [
                {
                    "id": self.erp_export_1.id,
                    "file_id": self.erp_export_1.file_id,
                    "from_date": localize(self.erp_export_1.from_date),
                    "to_date": localize(self.erp_export_1.to_date),
                    "created_at": localize(self.erp_export_1.created_at),
                    "count": DepositPayoutItem.objects.count(),
                    "actions": f'<a href="?file_id={self.file_id_1}" '
                    'class="btn btn-sm btn-primary">Download</a>',
                },
                {
                    "id": self.erp_export_2.id,
                    "file_id": self.erp_export_2.file_id,
                    "from_date": localize(self.erp_export_2.from_date),
                    "to_date": localize(self.erp_export_2.to_date),
                    "created_at": localize(self.erp_export_2.created_at),
                    "count": None,
                    "actions": f'<a href="?file_id={self.file_id_2}"'
                    ' class="btn btn-sm btn-primary">Download</a>',
                },
            ],
        )

    def test_get_file_with_items_returns_csv(self):
        # Act
        response = self._get_response(file_id=self.file_id_1)
        # Assert
        self.assertEqual(response["Content-Type"], "text/csv")
        # We expect 3 lines for each of the 2 deposit payout items, 6 lines total
        self._assert_csv_response(response, expected_length=6)

    def test_get_file_without_items_displays_message(self):
        # Act
        response = self._get_response(file_id=self.file_id_2)
        # Assert
        self._assert_response_is_redirect_with_message(
            response,
            _("Ingen linjer fundet for det angivne fil-ID"),
        )

    def test_get_unknown_file_id_returns_404(self):
        # Act
        response = self._get_response(file_id=uuid.uuid4())
        # Assert
        self.assertIsInstance(response, HttpResponseNotFound)
