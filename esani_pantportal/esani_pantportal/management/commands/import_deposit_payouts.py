# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import csv
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import paramiko
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from esani_pantportal.models import (
    DepositPayout,
    DepositPayoutItem,
    Product,
    RefundMethod,
)


def parse_csv_date(val, format="%Y%m%d") -> datetime.date:
    return datetime.strptime(val, format).date()


@dataclass
class TomraCSVFile:
    from_date: datetime.date
    to_date: datetime.date
    total_count: int
    items: list["TomraCSVFileLine"]


@dataclass
class TomraCSVFileLine:
    location_id: int
    rvm_serial: int
    date: datetime.date
    barcode: str
    count: int

    @classmethod
    def from_csv_row(cls, row):
        return cls(
            location_id=int(row[0]),
            rvm_serial=int(row[1]),
            date=parse_csv_date(row[2]),
            barcode=row[3],
            count=int(row[4]),
        )


class Command(BaseCommand):
    help = "Import deposit payout CSV files from Tomra"

    csv_delimiter = ";"

    def handle(self, **kwargs):
        source = LocalFilesystem(settings.TOMRA_PATH)

        for new_file in source.get_new_files():
            self.stdout.write(f"Processing new file {new_file}")
            with source.open(new_file) as input_stream:
                tomra_file = self._read_csv(input_stream)
                self._import_data(new_file, tomra_file)

        self.stdout.write("All done!")

    def _read_csv(self, input_stream):
        reader = csv.reader(input_stream, delimiter=self.csv_delimiter)

        file_header = next(reader)  # read file header
        next(reader)  # skip "csv header" (second line of file)

        tomra_file = TomraCSVFile(
            from_date=parse_csv_date(file_header[1]),
            to_date=parse_csv_date(file_header[2]),
            total_count=0,
            items=[],
        )

        tomra_lines = []
        total_count = 0

        for row in reader:
            if row[0].upper() != "COUNT":
                # We are not yet at last line in file. Parse it as a regular item
                tomra_lines.append(TomraCSVFileLine.from_csv_row(row))
            else:
                # We are at the last line in the CSV file, containing a total count
                total_count = int(row[1])

        # The "COUNT" at the end of the CSV file should equal the number of item lines,
        # plus the two header lines.
        assert total_count == len(tomra_lines) + 2

        tomra_file.items = tomra_lines
        tomra_file.total_count = total_count

        return tomra_file

    @transaction.atomic
    def _import_data(self, filename, tomra_file):
        deposit_payout = DepositPayout.objects.create(
            filename=filename,
            from_date=tomra_file.from_date,
            to_date=tomra_file.to_date,
            item_count=tomra_file.total_count,
        )
        DepositPayoutItem.objects.bulk_create(
            [
                DepositPayoutItem(
                    deposit_payout=deposit_payout,
                    kiosk=self._get_kiosk_from_rvm_serial(item.rvm_serial),
                    company_branch=self._get_company_branch_from_rvm_serial(
                        item.rvm_serial
                    ),
                    product=self._get_product_from_barcode(item.barcode),
                    location_id=item.location_id,
                    barcode=item.barcode,
                    rvm_serial=item.rvm_serial,
                    date=item.date,
                    count=item.count,
                )
                for item in tomra_file.items
            ]
        )

    def _get_refund_method_from_rvm_serial(self, rvm_serial):
        try:
            refund_method = RefundMethod.objects.get(serial_number=str(rvm_serial))
        except RefundMethod.DoesNotExist:
            self.stderr.write(f"Encountered unknown RVM serial number {rvm_serial}")
        else:
            return refund_method

    def _get_kiosk_from_rvm_serial(self, rvm_serial):
        refund_method = self._get_refund_method_from_rvm_serial(rvm_serial)
        if refund_method:
            return refund_method.kiosk

    def _get_company_branch_from_rvm_serial(self, rvm_serial):
        refund_method = self._get_refund_method_from_rvm_serial(rvm_serial)
        if refund_method:
            return refund_method.branch

    def _get_product_from_barcode(self, barcode):
        try:
            return Product.objects.get(barcode=str(barcode))
        except Product.DoesNotExist:
            self.stderr.write(f"Encountered unknown barcode {barcode}")


class Source(ABC):
    @abstractmethod
    def listdir(self):
        pass  # pragma: nocover

    @abstractmethod
    def open(self, filename):
        pass  # pragma: nocover

    def get_new_files(self):
        filenames = set(self.listdir())
        known_filenames = set(DepositPayout.objects.values_list("filename", flat=True))
        unknown_filenames = filenames - known_filenames
        return unknown_filenames


class SFTP(Source):
    def __init__(self, sftp_url: str):
        url = urlparse(sftp_url)
        ssh = self._get_ssh_client()
        # Automatically add keys without requiring human intervention
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=url.hostname,
            port=url.port,
            username=url.username,
            password=url.password,
        )
        ftp = ssh.open_sftp()
        ftp.chdir(url.path)
        self._ftp = ftp

    def listdir(self):
        return self._ftp.listdir()

    def open(self, filename):
        return self._ftp.open(filename)

    def _get_ssh_client(self):
        return paramiko.SSHClient()  # pragma: nocover


class LocalFilesystem(Source):
    def __init__(self, path: str):
        self._path = path

    def listdir(self):
        return os.listdir(self._path)

    def open(self, filename):
        return open(os.path.join(self._path, filename))
