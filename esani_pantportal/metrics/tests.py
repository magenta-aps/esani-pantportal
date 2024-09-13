# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from unittest.mock import MagicMock, patch

from django.test import TestCase


class MetricsTest(TestCase):
    def test_health_check_storage(self):
        resp = self.client.get("/metrics/health/storage")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"OK")

    @patch("tempfile.NamedTemporaryFile")
    def test_health_check_storage_value_error(self, mock_tempfile):
        mock_tempfile.read = MagicMock(return_value=b"invalid_content")

        resp = self.client.get("/metrics/health/storage")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content, b"ERROR")

    def test_health_check_database(self):
        resp = self.client.get("/metrics/health/database")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"OK")

    @patch("django.db.connection.ensure_connection")
    def test_health_check_database_exception(self, mock_ensure_connection):
        mock_ensure_connection.side_effect = Exception("Database connection failed")

        resp = self.client.get("/metrics/health/database")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content, b"ERROR")
