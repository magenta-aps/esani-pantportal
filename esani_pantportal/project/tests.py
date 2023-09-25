from unittest import TestCase

from project.util import json_dump


class UtilTest(TestCase):
    def test_json_dump(self):
        class NonSerializable:
            pass

        with self.assertRaises(TypeError):
            json_dump({"foo": NonSerializable()})
