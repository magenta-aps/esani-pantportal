# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import logging

from django.contrib.auth.models import AbstractUser
from ninja import Schema
from ninja_extra import NinjaExtraAPI, api_controller, http_post
from ninja_jwt.controller import TokenObtainPairController, TokenVerificationController
from ninja_jwt.schema import TokenObtainPairInputSchema, TokenObtainPairOutputSchema
from project.util import ORJSONRenderer

from esani_pantportal.api import ApprovedProductsAPI, QRBagAPI, QRStatusAPI
from esani_pantportal.apidoc_decorator import swagger_csp

logger = logging.getLogger(__name__)


class CustomTokenObtainPairOutputSchema(TokenObtainPairOutputSchema):
    fasttrack_enabled: bool


class CustomTokenObtainPairInputSchema(TokenObtainPairInputSchema):
    @classmethod
    def get_response_schema(cls) -> type[Schema]:
        return CustomTokenObtainPairOutputSchema

    @classmethod
    def get_token(cls, user: AbstractUser) -> dict:
        token = super().get_token(user)
        token["fasttrack_enabled"] = user.fasttrack_enabled
        return token


@api_controller("/token", tags=["Auth"])
class CustomJWTController(TokenVerificationController, TokenObtainPairController):
    @http_post(
        "/pair",
        response=CustomTokenObtainPairOutputSchema,
        url_name="token_obtain_pair",
    )
    def obtain_token(self, user_token: CustomTokenObtainPairInputSchema):
        user_token.check_user_authentication_rule()
        return user_token.to_response_schema()


api = NinjaExtraAPI(
    title="ESANI Pant",
    renderer=ORJSONRenderer(),
    csrf=False,
    docs_decorator=swagger_csp,
)
api.register_controllers(CustomJWTController)
api.register_controllers(ApprovedProductsAPI, QRBagAPI, QRStatusAPI)
