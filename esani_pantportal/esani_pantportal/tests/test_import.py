# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import io
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from esani_pantportal.forms import MultipleProductRegisterForm, ProductRegisterForm
from esani_pantportal.models import (
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    ImportJob,
    Product,
)
from esani_pantportal.util import default_dataframe

from .conftest import LoginMixin

ProductMock = MagicMock()

invalid_heights = [
    ("F", 84),
    ("F", 381),
    ("D", 79),
    ("D", 201),
    ("A", 79),
    ("A", 381),
]

invalid_capacities = [
    ("F", 149),
    ("F", 3001),
    ("D", 149),
    ("D", 1001),
    ("A", 149),
    ("A", 3001),
]

invalid_diameters = [
    ("F", 49),
    ("F", 131),
    ("D", 49),
    ("D", 101),
    ("A", 49),
    ("A", 131),
]


class MultipleProductRegisterFormTests(SimpleTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            "sep": ";",
            "sheet_name": "Ark1",
            "product_name_col": "Produktnavn [str]",
            "barcode_col": "Stregkode [str]",
            "refund_value_col": "Pantværdi [øre]",
            "material_col": "Materiale [str]",
            "height_col": "Højde [mm]",
            "diameter_col": "Diameter [mm]",
            "weight_col": "Vægt [g]",
            "capacity_col": "Volumen [ml]",
            "shape_col": "Form [str]",
            "danish_col": "Dansk pant [str]",
        }

    def make_excel_file_dict(self, df):
        output_stream = io.BytesIO()
        df.to_excel(output_stream, index=False, sheet_name="Ark1")
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        file = SimpleUploadedFile(
            "test_data.xlsx",
            output_stream.getvalue(),
            content_type=content_type,
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
        df.loc[0, "Volumen [ml]"] = -4
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_strings_in_integer_fields(self):
        df = default_dataframe()
        df.loc[0, "Volumen [ml]"] = "foo"
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_decimals_in_integer_fields(self):
        df = default_dataframe()
        df.loc[0, "Volumen [ml]"] = 2.4
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_invalid_diameter(self):
        df = default_dataframe()
        for shape, value in invalid_diameters:
            df.loc[0, "Diameter [mm]"] = value
            df.loc[0, "Form [str]"] = shape
            file = self.make_csv_file_dict(df)

            form = MultipleProductRegisterForm(self.defaults, file)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("diameter_col", form.errors)

    def test_import_csv_invalid_capacity(self):
        df = default_dataframe()
        for shape, value in invalid_capacities:
            df.loc[0, "Volumen [ml]"] = value
            df.loc[0, "Form [str]"] = shape
            file = self.make_csv_file_dict(df)

            form = MultipleProductRegisterForm(self.defaults, file)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("capacity_col", form.errors)

    def test_import_csv_invalid_height(self):
        df = default_dataframe()
        for shape, value in invalid_heights:
            df.loc[0, "Højde [mm]"] = value
            df.loc[0, "Form [str]"] = shape
            file = self.make_csv_file_dict(df)

            form = MultipleProductRegisterForm(self.defaults, file)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("height_col", form.errors)

    def test_import_csv_empty_integer_field(self):
        df = default_dataframe()
        df.loc[0, "Volumen [ml]"] = None
        file = self.make_csv_file_dict(df)

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("capacity_col", form.errors)

    def test_import_csv_exceeds_max_size(self):
        df = default_dataframe()
        df.loc[0, "Volumen [ml]"] = 2.4
        file = self.make_csv_file_dict(df)
        file["file"].size = 100000000000000000000

        form = MultipleProductRegisterForm(self.defaults, file)

        self.assertEquals(form.is_valid(), False)
        self.assertEquals(len(form.errors), 1)
        self.assertIn("file", form.errors)


class MultipleProductRegisterFormIntegrationTests(
    LoginMixin, TestCase, MultipleProductRegisterFormTests
):
    def test_view_post(self):
        self.login()
        df = default_dataframe()
        file = self.make_excel_file_dict(df)
        url = reverse("pant:product_multiple_register")
        data = self.defaults
        data["file"] = file["file"]
        self.assertFalse(ImportJob.objects.filter(file_name=file["file"]).exists())
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["success_count"], len(df))
        self.assertTrue(ImportJob.objects.filter(file_name=file["file"]).exists())

    def test_view_get(self):
        self.login("BranchAdmins")
        url = reverse("pant:product_multiple_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_post_access_denied(self):
        self.login("BranchUsers")
        df = default_dataframe()
        file = self.make_excel_file_dict(df)
        url = reverse("pant:product_multiple_register")
        data = self.defaults
        data["file"] = file["file"]
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_view_get_access_denied(self):
        self.login("BranchUsers")
        url = reverse("pant:product_multiple_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch("esani_pantportal.views.Product")
    def test_view_with_failures(self, ProductMock):
        self.login()

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
        url = reverse("pant:product_multiple_register")
        data = self.defaults
        data["file"] = file["file"]
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["failure_count"], 1)

    def test_view_with_existing_barcodes(self):
        self.login()
        df = default_dataframe()
        file = self.make_excel_file_dict(df)
        url = reverse("pant:product_multiple_register")

        data = self.defaults
        data["file"] = file["file"]

        Product.objects.create(
            barcode=df.loc[0, "Stregkode [str]"],
            product_name="foo",
            approved=False,
            material=PRODUCT_MATERIAL_CHOICES[0][0],
            height=100,
            diameter=50,
            weight=1,
            capacity=200,
            shape=PRODUCT_SHAPE_CHOICES[0][0],
        )

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["success_count"], len(df) - 1)
        self.assertEqual(response.context_data["existing_products_count"], 1)


class TemplateViewTests(LoginMixin, TestCase):
    def setUp(self) -> None:
        self.login()

    def assertEqualDf(self, df1, df2):
        for row in df1.index:
            for col in df1.columns:
                self.assertEqual(df1.loc[row, col], df2.loc[row, col])

    def test_csv_template_view(self):
        url = reverse("pant:csv_template_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = io.StringIO(str(response.content, "utf-8"))
        df = pd.read_csv(data, sep=";", dtype={"Stregkode [str]": str})
        self.assertEqualDf(df, default_dataframe())

    def test_excel_template_view(self):
        url = reverse("pant:excel_template_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        df = pd.read_excel(response.content, dtype={"Stregkode [str]": str})

        self.assertEqualDf(df, default_dataframe())

    def test_approved_product_csv_view(self):
        url = reverse("pant:registered_products_csv_download", kwargs={"approved": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_product_csv_view(self):
        url = reverse("pant:registered_products_csv_download", kwargs={"approved": 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestProductRegisterView(LoginMixin, TestCase):
    def setUp(self) -> None:
        self.login()

    def test_view(self):
        url = reverse("pant:product_register")

        data = {
            "product_name": "foo",
            "barcode": "12341234",
            "product_type": "Øl",
            "material": "P",
            "height": 100,
            "diameter": 100,
            "weight": 100,
            "capacity": 150,
            "shape": "F",
            "danish": "U",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("pant:product_register_success"))


class SingleProductRegisterFormTests(LoginMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            "product_name": "new_product",
            "barcode": "11221122",
            "refund_value": 200,
            "material": "P",
            "height": 200,
            "diameter": 100,
            "weight": 300,
            "capacity": 400,
            "shape": "F",
            "danish": "J",
        }

    def test_invalid_diameter(self):
        parameters = self.defaults
        for shape, value in invalid_diameters:
            parameters["diameter"] = value
            parameters["shape"] = shape

            form = ProductRegisterForm(parameters)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("diameter", form.errors)

    def test_invalid_height(self):
        parameters = self.defaults
        for shape, value in invalid_heights:
            parameters["height"] = value
            parameters["shape"] = shape

            form = ProductRegisterForm(parameters)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("height", form.errors)

    def test_invalid_capacity(self):
        parameters = self.defaults
        for shape, value in invalid_capacities:
            parameters["capacity"] = value
            parameters["shape"] = shape

            form = ProductRegisterForm(parameters)

            self.assertEquals(form.is_valid(), False)
            self.assertEquals(len(form.errors), 1)
            self.assertIn("capacity", form.errors)

    def test_view_get(self):
        self.login("BranchAdmins")
        url = reverse("pant:product_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_get_access_denied(self):
        self.login("BranchUsers")
        url = reverse("pant:product_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_view_post(self):
        self.login()
        url = reverse("pant:product_register")
        response = self.client.post(url, data=self.defaults)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        product_qs = Product.objects.filter(product_name="new_product")
        self.assertGreater(len(product_qs), 0)

    def test_view_post_access_denied(self):
        self.login("BranchUsers")
        url = reverse("pant:product_register")
        response = self.client.post(url, data=self.defaults)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
