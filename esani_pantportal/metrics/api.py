# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code="call-arg, attr-defined"

import logging
import tempfile

from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from ninja_extra import api_controller, route
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

log = logging.getLogger(__name__)


@api_controller(
    "/metrics",
    tags=["metrics"],
)
class MetricsAPI:
    @route.get("", url_name="metrics_prometheus")
    def get_all(self):
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    @route.get("/health/storage", url_name="metrics_health_storage")
    def health_storage(self):
        try:
            with tempfile.NamedTemporaryFile(
                dir=settings.MEDIA_ROOT, delete=True
            ) as temp_file:
                test_content = b"Test"
                temp_file.write(test_content)
                temp_file.flush()
                temp_file.seek(0)

                content = temp_file.read()
                if content != test_content:
                    raise ValueError(
                        (
                            "File content does not match, when trying to write and "
                            "read from file"
                        )
                    )

            return HttpResponse("OK")
        except Exception:
            log.exception("Storage health check failed")
            return HttpResponse("ERROR", status=500)

    @route.get("/health/database", url_name="metrics_health_database")
    def health_database(self):
        try:
            connection.ensure_connection()
            return HttpResponse("OK")
        except Exception:
            log.exception("Database health check failed")
            return HttpResponse("ERROR", status=500)
