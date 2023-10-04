# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from ninja_extra import NinjaExtraAPI
from project.util import ORJSONRenderer
from esani_pantportal.api import ApprovedProductsAPI

api = NinjaExtraAPI(title="ESANI Pant", renderer=ORJSONRenderer(), csrf=False)
api.register_controllers(ApprovedProductsAPI)
