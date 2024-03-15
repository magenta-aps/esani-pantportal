# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import logging

from django.http import HttpRequest, HttpResponse
from django_fsm import TransitionNotAllowed
from ninja_extra import NinjaExtraAPI, status
from ninja_jwt.controller import NinjaJWTDefaultController
from project.util import ORJSONRenderer

from esani_pantportal.api import ApprovedProductsAPI, QRBagAPI, QRStatusAPI

logger = logging.getLogger(__name__)


api = NinjaExtraAPI(title="ESANI Pant", renderer=ORJSONRenderer(), csrf=False)
api.register_controllers(NinjaJWTDefaultController)
api.register_controllers(ApprovedProductsAPI, QRBagAPI, QRStatusAPI)


@api.exception_handler(TransitionNotAllowed)
def handle_transition_not_allowed(
    request: HttpRequest,
    exc: TransitionNotAllowed,
) -> HttpResponse:
    logger.exception(
        "QRBag: id=%d qr=%s status=%s",
        exc.object.id,
        exc.object.qr,
        exc.object.status,
    )
    return api.create_response(
        request,
        {"detail": f"Cannot update status to {exc.object.status!r}"},
        status=status.HTTP_400_BAD_REQUEST,
    )
