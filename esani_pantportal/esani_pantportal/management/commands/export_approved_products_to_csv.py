import datetime
import os

import pandas as pd
from django.core.management.base import BaseCommand

from esani_pantportal.models import Product


class Command(BaseCommand):
    help = "Export approved products to csv"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Folder in which to save file")
        parser.add_argument(
            "--max_number_of_files",
            type=int,
            help="Number of files to allow in the output folder before cleaning up",
            default=20,
        )

    @staticmethod
    def make_filename():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_product_list.csv"

    @staticmethod
    def get_timestamp_from_filename(filename):
        return datetime.datetime.strptime(filename, "%Y%m%d_%H%M%S_product_list.csv")

    @staticmethod
    def export_all_approved_products(path, filename):
        """
        Loads all approved products and returns them as a pandas dataframe formatted
        according to https://redmine.magenta.dk/issues/57961
        """
        material_type_map = {
            "P": "PET",
            "A": "Aluminium",
            "S": "Steel",
            "G": "Glass",
        }

        column_map = {
            "barcode": "Barcode",
            "product_name": "ProductName",
            "material": "MaterialType",
            "height": "Height",
            "diameter": "Diameter",
            "weight": "Weight",
            "capacity": "Capacity",
            "shape": "Shape",
        }

        shape_map = {"F": "Bottle", "A": "Other"}

        all_products = list(
            Product.objects.filter(approved=True).values(
                "barcode",
                "product_name",
                "material",
                "height",
                "diameter",
                "weight",
                "capacity",
                "shape",
            )
        )

        df = pd.DataFrame(all_products)
        df = df.replace({"material": material_type_map, "shape": shape_map})
        df = df.rename(column_map, axis=1)
        df.to_csv(os.path.join(path, filename), sep=";", index=False)

    def get_files_to_clean(self, path, max_number_of_files):
        """
        Sort all csv files in the output folder and return the latest `n` files where
        n = max_number_of_files.
        """
        all_product_lists = sorted(
            [f for f in os.listdir(path) if f.endswith("product_list.csv")],
            key=self.get_timestamp_from_filename,
        )
        return all_product_lists[:-max_number_of_files]

    def cleanup(self, path, max_number_of_files):
        """
        Check how many files there are in the output folder and remove the oldest ones
        Only removes files if the amount of files exceeds `max_number_of_files`.
        """
        for product_list in self.get_files_to_clean(path, max_number_of_files):
            os.remove(os.path.join(path, product_list))

    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        max_number_of_files = kwargs["max_number_of_files"]
        filename = self.make_filename()

        self.export_all_approved_products(path, filename)
        self.cleanup(path, max_number_of_files)

        return filename
