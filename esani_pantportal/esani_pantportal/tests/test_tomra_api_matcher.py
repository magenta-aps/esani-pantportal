# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.test import TestCase

from esani_pantportal.clients.tomra.data_models import (
    ConsumerSession,
    Datum,
    Identity,
    Single,
)
from esani_pantportal.clients.tomra.matcher import Match, Matcher, NoMatch
from esani_pantportal.models import Product, QRBag


class TestMatcher(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.product = Product.objects.create(
            product_name="product_name",
            barcode="barcode",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            danish="J",
        )

        cls.bag = QRBag.objects.create(
            qr="bag_identity",
            active=True,
            # status="oprettet",
            # owner=user,
            # companybranch=companybranch,
            # kiosk=None,
        )

    def test_match(self):
        # Arrange
        datum = Datum(
            consumer_session=ConsumerSession(
                identity=Identity(bag_identity="bag_identity"),
                items=[Single(product_code="barcode")],
            )
        )
        # Act
        matcher = Matcher([datum])
        matches = list(matcher.match())
        # Assert
        self.assertEqual(len(matches), 1)
        self.assertIsInstance(matches[0], Match)
        self.assertEqual(matches[0].bag, self.bag)
        self.assertEqual(matches[0].product, self.product)

    def test_no_match_case_a(self):
        # Arrange
        datum = Datum(
            consumer_session=ConsumerSession(
                identity=Identity(bag_identity="unknown_bag_identity"),
                items=[Single(product_code="unknown_barcode")],
            )
        )
        # Act
        matcher = Matcher([datum])
        matches = list(matcher.match())
        # Assert
        self.assertEqual(len(matches), 1)
        self.assertIsInstance(matches[0], NoMatch)
        self.assertEqual(
            matches[0].message,
            "no match for bag_identity='unknown_bag_identity' "
            "and product_code='unknown_barcode'",
        )

    def test_no_match_case_b(self):
        # Arrange
        datum = Datum(
            consumer_session=ConsumerSession(
                identity=Identity(bag_identity="unknown_bag_identity"),
                items=[Single(product_code=None)],
            )
        )
        # Act
        matcher = Matcher([datum])
        matches = list(matcher.match())
        # Assert
        self.assertEqual(len(matches), 1)
        self.assertIsInstance(matches[0], NoMatch)
        self.assertTrue(matches[0].message.startswith("no product_code on item="))

    def test_no_match_case_c(self):
        # Arrange
        datum = Datum(
            consumer_session=ConsumerSession(
                identity=None,
                items=[Single(product_code="barcode")],
            )
        )
        # Act
        matcher = Matcher([datum])
        matches = list(matcher.match())
        # Assert
        self.assertEqual(len(matches), 1)
        self.assertIsInstance(matches[0], NoMatch)
        self.assertTrue(
            matches[0].message.startswith("no identity on session.consumer_session.id=")
        )
