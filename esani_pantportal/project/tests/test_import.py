# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import io
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.forms import MultipleProductRegisterForm
from esani_pantportal.util import default_dataframe

from esani_pantportal.models import (  # isort: skip
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    Product,
)


ProductMock = MagicMock()


class MultipleProductRegisterFormTests(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            "sep": ";",
            "sheet_name": "Ark1",
            "product_name_col": "Produktnavn [str]",
            "barcode_col": "Stregkode [str]",
            "refund_value_col": "Pantværdi [øre]",
            "tax_group_col": "Afgiftsgruppe [int]",
            "product_type_col": "Vareart [str]",
            "material_type_col": "Materialetype [str]",
            "height_col": "Højde [mm]",
            "diameter_col": "Diameter [mm]",
            "weight_col": "Vægt [g]",
            "capacity_col": "Volumenkapacitet [ml]",
            "shape_col": "Form [str]",
        }

    def make_excel_file_dict(self, df):
        output_stream = io.BytesIO()
        df.to_excel(output_stream, index=False, sheet_name="Ark1")
        file = SimpleUploadedFile(
            "test_data.xlsx",
            output_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return {"file": file}

    def make_csv_file_dict(self, df, sep=";", filename="test_data.csv"):
        output_stream = io.BytesIO()
        df.to_csv(output_stream, sep=sep)
        file = SimpleUploadedFile(
            filename,
            output_stream.getvalue(),
            content_type="text/csv",
        )
        return {"file": file}

    def test_import_excel_file(self):
        df = default_dataframe()
        file = self.make_excel_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)
        self.assertEquals(form.is_valid(), True)

    def test_import_csv_file(self):
        df = default_dataframe()
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)
        self.assertEquals(form.is_valid(), True)

    def test_import_csv_file_wrong_separator(self):
        df = default_dataframe()
        file = self.make_csv_file_dict(df, sep=",")

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("sep", form.errors)

    def test_import_excel_file_wrong_sheet(self):
        df = default_dataframe()
        file = self.make_excel_file_dict(df)

        inputs = self.defaults
        inputs["sheet_name"] = "wrong_sheet"
        form = MultipleProductRegisterForm(inputs, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("file", form.errors)

    def test_import_csv_file_wrong_extension(self):
        df = default_dataframe()
        file = self.make_csv_file_dict(df, filename="nudes.jpg")

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("file", form.errors)

    def test_import_csv_wrong_column_mapping(self):
        df = default_dataframe()
        file = self.make_csv_file_dict(df)

        inputs = self.defaults
        inputs["barcode_col"] = "wrong_column"
        form = MultipleProductRegisterForm(inputs, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("barcode_col", form.errors)

    def test_import_csv_wrong_column_contents(self):
        df = default_dataframe()
        df.loc[2, "Form [str]"] = "X"
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("shape_col", form.errors)

    def test_import_csv_invalid_barcode(self):
        df = default_dataframe()
        df.loc[2, "Stregkode [str]"] = "xxxx"  # Contains non-digits
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("barcode_col", form.errors)

    def test_import_csv_invalid_barcode_length(self):
        df = default_dataframe()
        df.loc[2, "Stregkode [str]"] = "1234"  # Too short
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("barcode_col", form.errors)

    def test_import_csv_duplice_barcodes(self):
        df = default_dataframe()
        df.loc[0, "Stregkode [str]"] = "12341234"
        df.loc[1, "Stregkode [str]"] = "12341234"
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("barcode_col", form.errors)

    def test_import_csv_multiple_duplice_barcodes(self):
        df = default_dataframe()
        df.loc[0, "Stregkode [str]"] = "12341234"
        df.loc[1, "Stregkode [str]"] = "12341234"
        df.loc[2, "Stregkode [str]"] = "12341235"
        df.loc[3, "Stregkode [str]"] = "12341235"
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("barcode_col", form.errors)

    def test_import_csv_negative_value_in_integer_fields(self):
        df = default_dataframe()
        df.loc[0, "Volumenkapacitet [ml]"] = -4
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_strings_in_integer_fields(self):
        df = default_dataframe()
        df.loc[0, "Volumenkapacitet [ml]"] = "foo"
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_decimals_in_integer_fields(self):
        df = default_dataframe()
        df.loc[0, "Volumenkapacitet [ml]"] = 2.4
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_empty_integer_field(self):
        df = default_dataframe()
        df.loc[0, "Volumenkapacitet [ml]"] = None
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_exceeds_max_size(self):
        df = default_dataframe()
        df.loc[0, "Volumenkapacitet [ml]"] = 2.4
        file = self.make_csv_file_dict(df)
        file["file"].size = 100000000000000000000

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("file", form.errors)

    def test_view(self):
        df = default_dataframe()
        file = self.make_excel_file_dict(df)
        url = reverse("pant:multiple_product_register") + "?login_bypass=1"
        data = self.defaults
        data["file"] = file["file"]
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["success_count"], len(df))

    @patch("esani_pantportal.views.Product")
    def test_view_with_failures(self, ProductMock):
        # Simulate that someone implements a new condition, which rejects all products
        # with a height over 100 mm. But forgets to update the corresponding form
        # methods.
        def init(*args, **kwargs):
            if kwargs["height"] > 100:
                raise ValidationError({"height": "products over 100 mm are evil."})
            else:
                return MagicMock()

        ProductMock.side_effect = init

        df = default_dataframe()
        df["Højde [mm]"] = [200, 100, 100, 100]

        file = self.make_excel_file_dict(df)
        url = reverse("pant:multiple_product_register") + "?login_bypass=1"
        data = self.defaults
        data["file"] = file["file"]
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["failure_count"], 1)

    def test_view_with_existing_barcodes(self):
        df = default_dataframe()
        file = self.make_excel_file_dict(df)
        url = reverse("pant:multiple_product_register") + "?login_bypass=1"

        data = self.defaults
        data["file"] = file["file"]

        Product.objects.create(
            barcode=df.loc[0, "Stregkode [str]"],
            product_name="foo",
            tax_group=1,
            product_type="root beer",
            approved=False,
            material_type=PRODUCT_MATERIAL_CHOICES[0][0],
            height=1,
            diameter=1,
            weight=1,
            capacity=1,
            shape=PRODUCT_SHAPE_CHOICES[0][0],
        )

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["success_count"], len(df) - 1)
        self.assertEqual(response.context_data["existing_products_count"], 1)


class TemplateViewTests(TestCase):
    def assertEqualDf(self, df1, df2):
        for row in df1.index:
            for col in df1.columns:
                self.assertEqual(df1.loc[row, col], df2.loc[row, col])

    def test_csv_template_view(self):
        url = reverse("pant:example_csv") + "?login_bypass=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = io.StringIO(str(response.content, "utf-8"))
        df = pd.read_csv(data, sep=";", dtype={"Stregkode [str]": str})
        self.assertEqualDf(df, default_dataframe())

    def test_excel_template_view(self):
        url = reverse("pant:example_excel") + "?login_bypass=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        df = pd.read_excel(response.content, dtype={"Stregkode [str]": str})

        self.assertEqualDf(df, default_dataframe())
