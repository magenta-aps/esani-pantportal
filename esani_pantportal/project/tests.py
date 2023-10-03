# SPDX-FileCopyrightText: 2023 Magenta 2023
#
# SPDX-License-Identifier: MPL-2.0

from unittest import TestCase

from project.util import json_dump


class UtilTest(TestCase):
    def test_json_dump(self):
        class NonSerializable:
            pass

        with self.assertRaises(TypeError):
            json_dump({"foo": NonSerializable()})
