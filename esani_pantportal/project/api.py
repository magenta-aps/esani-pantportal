# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import logging

from django.contrib.auth.models import AbstractUser
from ninja import Schema
from ninja_extra import NinjaExtraAPI, api_controller, http_post
from ninja_jwt.controller import TokenObtainPairController, TokenVerificationController
from ninja_jwt.schema import (
    TokenObtainPairInputSchema,
    TokenObtainPairOutputSchema,
    TokenRefreshInputSchema,
    TokenRefreshOutputSchema,
)
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.utils import token_error
from project.util import ORJSONRenderer
from pydantic import model_validator

from esani_pantportal.api import ApprovedProductsAPI, QRBagAPI, QRStatusAPI
from esani_pantportal.apidoc_decorator import swagger_csp
from esani_pantportal.models import User

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


class CustomTokenRefreshOutputSchema(TokenRefreshOutputSchema):
    fasttrack_enabled: bool


class CustomTokenRefreshInputSchema(TokenRefreshInputSchema):
    fasttrack_enabled: bool = False

    @classmethod
    def get_response_schema(cls) -> type[Schema]:
        return CustomTokenRefreshOutputSchema

    @model_validator(mode="after")
    @token_error
    def validate_schema(cls, values: "CustomTokenRefreshInputSchema"):
        refresh = RefreshToken(values.refresh)
        try:
            user_pk = refresh["user_id"]
            user = User.objects.get(pk=user_pk)
        except (KeyError, User.DoesNotExist):
            values.fasttrack_enabled = False
        else:
            values.fasttrack_enabled = user.fasttrack_enabled
        return super().validate_schema(values)


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

    @http_post(
        "/refresh",
        response=CustomTokenRefreshOutputSchema,
        url_name="token_refresh",
    )
    def refresh_token(self, refresh_token: CustomTokenRefreshInputSchema):
        return refresh_token.to_response_schema()


api = NinjaExtraAPI(
    title="ESANI Pant",
    renderer=ORJSONRenderer(),
    csrf=False,
    docs_decorator=swagger_csp,
)
api.register_controllers(CustomJWTController)
api.register_controllers(ApprovedProductsAPI, QRBagAPI, QRStatusAPI)
