# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import re

from bs4 import BeautifulSoup
from django.test import TestCase


class ApiDocTest(TestCase):

    def test_nonce(self):
        response = self.client.get("/api/docs")
        nonce = re.search(
            r"'(nonce-[\w+=]+)'",
            response.headers["Content-Security-Policy"],
        ).group(1)
        self.assertIsNotNone(nonce)
        dom = BeautifulSoup(response.content, "html.parser")
        for script_tag in dom.find_all("script"):
            self.assertTrue(script_tag.has_attr("nonce"))
            self.assertEqual(script_tag["nonce"], nonce)
        for script_tag in dom.find_all("link"):
            self.assertTrue(script_tag.has_attr("nonce"))
            self.assertEqual(script_tag["nonce"], nonce)
