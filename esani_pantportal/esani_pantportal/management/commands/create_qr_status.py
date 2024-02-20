# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.core.management.base import BaseCommand

from esani_pantportal.models import QRStatus


class Command(BaseCommand):
    help = "Create QR Bag status objects"

    def handle(self, *args, **options):
        QRStatus.objects.update_or_create(
            code="butik_oprettet",
            defaults={
                "name_da": "Oprettet af forhandler",
                "name_kl": "Oprettet af forhandler",
            },
        )
        QRStatus.objects.update_or_create(
            code="pantsystem_modtaget",
            defaults={
                "name_da": "Modtaget af pantsystemet",
                "name_kl": "Modtaget af pantsystemet",
            },
        )
        QRStatus.objects.update_or_create(
            code="backbone_modtaget",
            defaults={
                "name_da": "Modtaget af Backbone",
                "name_kl": "Modtaget af Backbone",
            },
        )
        QRStatus.objects.update_or_create(
            code="esani_modtaget",
            defaults={
                "name_da": "Modtaget af ESANI",
                "name_kl": "Modtaget af ESANI",
            },
        )
        QRStatus.objects.update_or_create(
            code="esani_optalt",
            defaults={
                "name_da": "Optalt hos ESANI",
                "name_kl": "Optalt hos ESANI",
            },
        )
        QRStatus.objects.update_or_create(
            code="esani_udbetalt",
            defaults={
                "name_da": "Udbetalt af ESANI",
                "name_kl": "Udbetalt af ESANI",
            },
        )
