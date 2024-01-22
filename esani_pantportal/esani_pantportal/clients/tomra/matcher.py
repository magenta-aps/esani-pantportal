# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from dataclasses import dataclass

from esani_pantportal.models import Product, QRBag


@dataclass(frozen=True)
class Result:
    pass


@dataclass(frozen=True)
class Match(Result):
    bag: QRBag
    product: Product


@dataclass(frozen=True)
class NoMatch(Result):
    message: str


class Matcher:
    """
    A `Matcher` attempts to match a set of Tomra consumer sessions against
    the QR bags and products that are registered in Pantportalen.

    Intended usage:
    >>> from esani_pantportal.clients.tomra.api import TomraAPI
    >>> from esani_pantportal.clients.tomra.matcher import Matcher
    >>> api = TomraAPI.from_settings()
    >>> matches = Matcher(api.get_consumer_sessions(datetime(2024, 1)))
    """

    def __init__(self, consumer_sessions):
        self._consumer_sessions = consumer_sessions

    def match(self):
        product_map = {product.barcode: product for product in Product.objects.all()}
        bag_map = {bag.qr: bag for bag in QRBag.objects.all()}

        for session in self._consumer_sessions:
            if session.consumer_session.identity is not None:
                bag_identity = session.consumer_session.identity.bag_identity
                for item in session.consumer_session.items:
                    product_code = item.product_code
                    if product_code:
                        if product_code in product_map and bag_identity in bag_map:
                            yield Match(
                                bag_map[bag_identity],
                                product_map[product_code],
                            )
                        else:
                            yield NoMatch(
                                f"no match for {bag_identity=} and {product_code=}",
                            )
                    else:
                        yield NoMatch(f"no product_code on {item=}")
            else:
                yield NoMatch(f"no identity on {session.consumer_session.id=}")
