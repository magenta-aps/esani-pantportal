# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import json
from datetime import datetime
from typing import Optional

from django.db import IntegrityError
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from ninja import Field, FilterSchema, ModelSchema, Query
from ninja_extra import api_controller, permissions, route
from ninja_extra.pagination import paginate
from ninja_extra.schemas import NinjaPaginationResponseSchema
from ninja_jwt.authentication import JWTAuth

from esani_pantportal.models import Product, QRBag


class ApprovedProductsOut(ModelSchema):
    class Config:
        model = Product
        model_fields = [
            "product_name",
            "barcode",
        ]


class ApprovedProductsFilterSchema(FilterSchema):
    product_name: Optional[str]
    barcode: Optional[int]


@api_controller(
    "/produkter",
    tags=["Produkter"],
    permissions=[permissions.IsAuthenticatedOrReadOnly],
)
class ApprovedProductsAPI:
    @route.get(
        "",
        response=NinjaPaginationResponseSchema[ApprovedProductsOut],
        url_name="godkendt_liste",
        summary="Liste over produkter registreret hos ESANI A/S",
    )
    @paginate()
    def list_approved_products(
        self,
        filters: ApprovedProductsFilterSchema = Query(...),
        sort: str = None,
        order: str = None,
    ):
        qs = filters.filter(Product.objects.filter(approved=True))
        qs.order_by("product_name", "barcode")

        return list(qs)


class QRBagIn(ModelSchema):
    class Config:
        model = QRBag
        model_fields = [
            "active",
            "status",
        ]
        model_fields_optional = ["active", "status"]


class QRBagOut(ModelSchema):
    owner: str = Field(..., alias="owner.username")

    class Config:
        model = QRBag
        model_fields = [
            "qr",
            "active",
            "status",
            "updated",
        ]


class QRBagHistoryOut(QRBagOut):
    history_date: datetime


@api_controller(
    "/qrbag",
    tags=["QR-Pose"],
    permissions=[permissions.IsAuthenticatedOrReadOnly],
)
class QRBagAPI:
    @route.get(
        "/{qr}",
        response=QRBagOut,
        url_name="qrbag_get",
        summary="QR-pose ud fra kode",
    )
    def get(self, qr: str):
        try:
            return get_object_or_404(QRBag, qr=qr)
        except Http404:
            raise

    @route.post(
        "/{qr}",
        auth=JWTAuth(),
        url_name="qrbag_create",
        summary="Opret QR-pose",
        response=QRBagOut,
    )
    def create(self, qr: str, payload: QRBagIn):
        try:
            return QRBag.objects.create(
                **payload.dict(), qr=qr, owner=self.context.request.user
            )
        except IntegrityError:
            return HttpResponseBadRequest(
                json.dumps({"error": f"qr {qr} already exists"})
            )

    @route.patch(
        "/{qr}",
        auth=JWTAuth(),
        url_name="qrbag_update",
        summary="Opdatér QR-pose",
        response=QRBagOut,
    )
    def update(self, qr: str, payload: QRBagIn):
        try:
            item = QRBag.objects.get(qr=qr)
        except QRBag.DoesNotExist:
            return self.create(qr, payload)
        data = payload.dict(exclude_unset=True)
        for attr, value in data.items():
            setattr(item, attr, value)
        item.owner = self.context.request.user
        item.save()
        return item

    @route.get(
        "/{qr}/history",
        response=NinjaPaginationResponseSchema[QRBagHistoryOut],
        auth=JWTAuth(),
        url_name="qrbag_history",
    )
    @paginate()  # https://eadwincode.github.io/django-ninja-extra/tutorial/pagination/
    def history(self, qr: str):
        item = get_object_or_404(QRBag, qr=qr)
        return list(item.history.order_by("history_date"))
