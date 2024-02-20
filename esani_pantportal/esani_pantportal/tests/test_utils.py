# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from project.util import json_dump

from esani_pantportal.migrations.utils.utils import clean_phone_no
from esani_pantportal.util import (
    add_parameters_to_url,
    clean_url,
    default_dataframe,
    float_to_string,
    join_strings_human_readable,
    make_valid_choices_str,
    read_csv,
    read_excel,
    remove_parameter_from_url,
)


class UtilTest(SimpleTestCase):
    def test_json_dump(self):
        class NonSerializable:
            pass

        with self.assertRaises(TypeError):
            json_dump({"foo": NonSerializable()})

    def test_import_unreadable_csv_file(self):
        with self.assertRaises(ValidationError):
            read_csv(None)

    def test_import_unreadable_excel_file(self):
        with self.assertRaises(ValidationError):
            read_excel(None)

    def test_default_dataframe(self):
        df = default_dataframe()

        self.assertEqual(df.shape[0], 4)
        self.assertEqual(df.shape[1], 9)

    def test_join_strings_human_readable(self):
        string = join_strings_human_readable(["foo", "bar"])
        self.assertEqual(string, "foo og bar")

        string = join_strings_human_readable(["foo", "mucki", "bar"])
        self.assertEqual(string, "foo, mucki og bar")

        string = join_strings_human_readable(["foo"])
        self.assertEqual(string, "foo")

        string = join_strings_human_readable([])
        self.assertEqual(string, "")

    def test_make_valid_choices_str(self):
        choices = [(1, "foo"), (2, "mucki"), (3, "bar")]
        string = make_valid_choices_str(choices)
        self.assertEqual(string, "'1' (foo), '2' (mucki) og '3' (bar)")

    def test_remove_parameter_from_url(self):
        url = "http://foo.com/?foo=2&bar=4"
        self.assertEqual(remove_parameter_from_url(url, "foo"), "http://foo.com/?bar=4")
        self.assertEqual(remove_parameter_from_url(url, "bar"), "http://foo.com/?foo=2")

        url = "http://foo.com/"
        self.assertEqual(remove_parameter_from_url(url, "foo"), "http://foo.com/")

        url = "http://foo.com/?foo=2"
        self.assertEqual(remove_parameter_from_url(url, "fod"), "http://foo.com/?foo=2")

        url = "relative_url/?foo=2&bar=4"
        self.assertEqual(remove_parameter_from_url(url, "foo"), "relative_url/?bar=4")
        self.assertEqual(remove_parameter_from_url(url, "bar"), "relative_url/?foo=2")

    def test_float_to_string(self):
        self.assertEqual(float_to_string(2.1), "2,1")
        self.assertEqual(float_to_string(2.0), "2")

    def test_add_parameters_to_url(self):
        url = "http://foo.com/"
        params = {"s": 1}
        self.assertEqual(add_parameters_to_url(url, params), "http://foo.com/?s=1")

        url = "http://foo.com/?m=2"
        self.assertEqual(add_parameters_to_url(url, params), "http://foo.com/?m=2&s=1")

    def test_phone_no_cleaner(self):
        self.assertEqual(clean_phone_no("112211"), "(+299) 112211")
        self.assertEqual(clean_phone_no("11 22 11"), "(+299) 112211")
        self.assertEqual(clean_phone_no("(+299) 11 22 11"), "(+299) 112211")
        self.assertEqual(clean_phone_no("299 11 22 11"), "(+299) 112211")
        self.assertEqual(clean_phone_no("+299 11 22 11"), "(+299) 112211")
        self.assertEqual(clean_phone_no("(+299) 112211"), "(+299) 112211")

        self.assertEqual(clean_phone_no("11221122"), "(+45) 11221122")
        self.assertEqual(clean_phone_no("11 22 11 22"), "(+45) 11221122")
        self.assertEqual(clean_phone_no("(+45) 11 22 11 22"), "(+45) 11221122")
        self.assertEqual(clean_phone_no("45 11 22 11 22"), "(+45) 11221122")
        self.assertEqual(clean_phone_no("+45 11 22 11 22"), "(+45) 11221122")
        self.assertEqual(clean_phone_no("(+45) 11221122"), "(+45) 11221122")

        self.assertEqual(clean_phone_no("+299 36 35 04"), "(+299) 363504")
        self.assertEqual(clean_phone_no("00299558835"), "(+299) 558835")
        self.assertEqual(clean_phone_no("004511221122"), "(+45) 11221122")

    def test_clean_url(self):
        self.assertEqual(clean_url("http://foo.com?id=1&id=2"), "http://foo.com?id=2")
        self.assertEqual(clean_url("http://foo.com?id=1"), "http://foo.com?id=1")
        self.assertEqual(clean_url("http://foo.com"), "http://foo.com")
