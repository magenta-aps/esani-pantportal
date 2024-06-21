# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from unittest.mock import MagicMock, patch

from django.test import TestCase
from prometheus_client import generate_latest


class MetricsAPITest(TestCase):
    def test_get_all(self):
        resp = self.client.get("/api/metrics")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, generate_latest())

    def test_health_storage(self):
        resp = self.client.get("/api/metrics/health/storage")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"OK")
