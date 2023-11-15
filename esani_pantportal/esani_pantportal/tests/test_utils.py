# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.core.exceptions import ValidationError
from django.test import TestCase
from project.util import json_dump

from esani_pantportal.util import (  # isort: skip
    read_csv,
    read_excel,
    join_strings_human_readable,
    make_valid_choices_str,
    default_dataframe,
    remove_parameter_from_url,
)


class UtilTest(TestCase):
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
