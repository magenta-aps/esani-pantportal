# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import uuid
from io import BytesIO

import openpyxl
from django import forms
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext_lazy as _

from esani_pantportal.forms import SortPaginateForm
from esani_pantportal.models import ESANI_USER, ERPCreditNoteExport, User
from esani_pantportal.views import SearchView


class FormImpl(SortPaginateForm):
    search = forms.CharField(required=False)
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
    # Specify the model fields to use for exact matching
    search_fields_exact = ["from_date"]

    def render_to_response(self, context, **response_kwargs):
        return TemplateResponse(self.request, "", context=context, **response_kwargs)

    def get_view_name(self) -> str:
        return "Dummy implementation"


class SearchViewSearchFieldsImpl(SearchViewImpl):
    # Specify the fields to use for similarity search
    search_fields = ["created_by__username", "created_by__phone"]


class TestSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.uuid = uuid.uuid4()
        cls.user, _ = User.objects.get_or_create(
            username="erp user",
            user_type=ESANI_USER,
        )
        cls.export = ERPCreditNoteExport.objects.create(
            file_id=cls.uuid,
            from_date=datetime.date(2020, 1, 1),
            to_date=datetime.date(2020, 2, 1),
            created_by=cls.user,
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

    def test_similarity_search_finds_object_via_username(self):
        # Using a `search` input which is sufficiently similar to the username
        # "erp user" should return the matching object.
        view, response = self._get_view_instance(
            view_class=SearchViewSearchFieldsImpl,
            search="era",
        )
        self._assert_match_found(response)

    def test_similarity_search_finds_nothing(self):
        view, response = self._get_view_instance(
            view_class=SearchViewSearchFieldsImpl,
            search="foo",
        )
        self._assert_no_matches(response)

    def test_similarity_search_handles_no_search_fields_defined(self):
        view, response = self._get_view_instance(
            view_class=SearchViewImpl,
            from_date=datetime.date(2020, 2, 2),
            search="foo",
        )
        self._assert_no_matches(response)

    def _assert_match_found(self, response):
        self.assertListEqual(
            response.context_data["items"],
            [
                {
                    "id": self.export.pk,
                    "file_id": self.export.file_id,
                    "from_date": self.export.from_date,
                }
            ],
        )

    def _assert_no_matches(self, response):
        self.assertListEqual(response.context_data["items"], [])

    def _get_view_instance(self, **kwargs) -> tuple[SearchViewImpl, HttpResponse]:
        view_class = kwargs.pop("view_class", SearchViewImpl)
        request = RequestFactory().get("", data=kwargs)
        view = view_class()
        view.setup(request)
        response = view.get(request)
        return view, response
