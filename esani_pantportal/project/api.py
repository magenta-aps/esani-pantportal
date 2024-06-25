# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from project.util import ORJSONRenderer

from esani_pantportal.api import ApprovedProductsAPI, QRBagAPI, QRStatusAPI

api = NinjaExtraAPI(title="ESANI Pant", renderer=ORJSONRenderer(), csrf=False)
api.register_controllers(NinjaJWTDefaultController)
api.register_controllers(ApprovedProductsAPI, QRBagAPI, QRStatusAPI)
