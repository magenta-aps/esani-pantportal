# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import csv
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from esani_pantportal.models import QRCodeGenerator


class Command(BaseCommand):
    help = "Generate QR codes for return bags"

    def add_arguments(self, parser):
        parser.add_argument(
            "bag_type", type=str, help="Type of bags to print QR codes for"
        )
        parser.add_argument(
            "number_of_codes",
            type=int,
            help="Number of QR codes to generate",
        )

    def handle(self, bag_type, number_of_codes, **kwargs):
        try:
            qr_generator, _ = QRCodeGenerator.objects.get_or_create(
                **settings.QR_GENERATOR_SERIES[bag_type]
            )
        except KeyError:
            available_types = [key for key in settings.QR_GENERATOR_SERIES.keys()]
            raise CommandError(
                f"Bag type {bag_type} does not exist.\n"
                + f"Available options are: {available_types}"
            )
        if number_of_codes <= 0:
            raise CommandError("Number of codes to generate must be > 0")

        qr_codes = qr_generator.generate_qr_codes(number_of_codes)

        today = date.today().isoformat()
        count = qr_generator.count
        filename = f"{bag_type}-{today}_{number_of_codes}-codes_of_{count}.csv"
        output_path = f"{settings.QR_OUTPUT_DIR}/{filename}"
        with open(output_path, "w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["QR-kode", "Id", "Kontrolkode"])
            for qr_code in qr_codes:
                id_and_cc = qr_code.removeprefix(
                    f"{settings.QR_URL_PREFIX}{qr_generator.prefix}"
                )
                qr_id = id_and_cc[0 : settings.QR_ID_LENGTH]
                control_code = id_and_cc[settings.QR_ID_LENGTH :]
                writer.writerow([qr_code, qr_id, control_code])

        return output_path
