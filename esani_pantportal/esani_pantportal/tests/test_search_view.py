# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import uuid
from io import BytesIO

import openpyxl
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext_lazy as _

from esani_pantportal.forms import SortPaginateForm
from esani_pantportal.models import ERPCreditNoteExport
from esani_pantportal.views import SearchView


class FormImpl(SortPaginateForm):
    from_date = forms.DateField(required=False)


class SearchViewImpl(SearchView):
    # Use the `ERPCreditNoteExport` model as it has a UUID field
    model = ERPCreditNoteExport
    # Provide dummy filter form
    form_class = FormImpl
    # Specify the column(s) to export to Excel
    fixed_columns = {
        "file_id": _("Fil-ID"),
        "from_date": _("Fra-dato"),
    }

    def get_view_name(self) -> str:
        return "Dummy implementation"


class TestSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.uuid = uuid.uuid4()
        cls.export = ERPCreditNoteExport.objects.create(
            file_id=cls.uuid,
            from_date=datetime.date(2020, 1, 1),
            to_date=datetime.date(2020, 2, 1),
        )

    def test_get_excel_format(self):
        view, response = self._get_view_instance(format="excel")
        self.assertIsNotNone(response["Content-Disposition"])
        workbook = openpyxl.open(BytesIO(response.content))
        sheet = workbook.active
        # Assert: verify header
        self.assertEqual(sheet["A1"].value, "Fil-ID")
        self.assertEqual(sheet["B1"].value, "Fra-dato")
        # Assert: verify first (and only) data row
        self.assertEqual(sheet["A2"].value, str(self.uuid))
        self.assertEqual(sheet["B2"].value, datetime.datetime(2020, 1, 1, 0, 0, 0))

    def _get_view_instance(self, **kwargs) -> tuple[SearchViewImpl, HttpResponse]:
        request = RequestFactory().get("", data=kwargs)
        view = SearchViewImpl()
        view.setup(request)
        response = view.get(request)
        return view, response
