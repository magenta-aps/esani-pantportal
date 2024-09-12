# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

JOB_EXEC_TIME_REGISTRY = CollectorRegistry()
JOB_EXEC_TIME = Gauge(
    "groenland_job",
    "Latest execution time",
    registry=JOB_EXEC_TIME_REGISTRY,
)


def push_groenland_job_metric(job_name: str):
    try:
        JOB_EXEC_TIME.set_to_current_time()
        push_to_gateway(
            settings.PROMETHEUS_PUSHGATEWAY_HOST,
            job=job_name,
            registry=JOB_EXEC_TIME_REGISTRY,
        )
    except Exception as e:
        print(
            (
                "Unable to push metrics to "
                f"prometheus-pushgateway: {settings.PROMETHEUS_PUSHGATEWAY_HOST}",
                str(e),
            )
        )
        # raise e
