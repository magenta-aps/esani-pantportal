# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from psycopg2 import OperationalError as PsycopgOpError
from time import sleep


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            try:
                conn = connections["default"]
            except (OperationalError, PsycopgOpError):
                print("waiting for database to come online!")
                sleep(1)
            else:
                conn.close()
                print("database online")
                break
