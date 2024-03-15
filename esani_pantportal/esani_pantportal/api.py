# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import json
from datetime import datetime
from typing import List, Optional

from django.db import IntegrityError
from django.http import Http404, HttpRequest, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from ninja import FilterSchema, ModelSchema, Query
from ninja_extra import ControllerBase, api_controller, permissions, route, status
from ninja_extra.exceptions import APIException
from ninja_extra.pagination import paginate
from ninja_extra.schemas import NinjaPaginationResponseSchema
from ninja_jwt.authentication import JWTAuth

from esani_pantportal.models import (
    CompanyBranch,
    Kiosk,
    Product,
    QRBag,
    QRCodeGenerator,
    QRStatus,
)


class DjangoPermission(permissions.BasePermission):
    method_map = {
        "GET": "view",
        "POST": "add",
        "PATCH": "change",
        "DELETE": "delete",
    }

    def __init__(self, appname, modelname):
        super().__init__()
        self.appname = appname
        self.modelname = modelname

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        method = str(request.method)
        operation = self.method_map[method]
        return request.user.has_perm(f"{self.appname}.{operation}_{self.modelname}")


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
class ApprovedProductsAPI:  # type: ignore [call-arg]
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
        sort: str | None = None,
        order: str | None = None,
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
    owner: str
    company: str

    class Config:
        model = QRBag
        model_fields = [
            "qr",
            "active",
            "status",
            "updated",
        ]

    @staticmethod
    def resolve_owner(obj: QRBag):
        return getattr(obj.owner, "username")

    @staticmethod
    def resolve_company(obj: QRBag):
        if obj.kiosk:
            return obj.kiosk.name
        elif obj.company_branch:
            return obj.company_branch.name


class QRBagHistoryOut(QRBagOut):
    history_date: datetime


class InvalidQRBagStatus(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, value) -> None:
        self.detail = f"Invalid value {value!r} for status"


class StatusChangeNotAllowed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, value) -> None:
        self.detail = f"This user is not allowed to set status to {value!r}"


@api_controller(
    "/qrbag",
    tags=["QR-Pose"],
    permissions=[
        permissions.IsAuthenticatedOrReadOnly,
        DjangoPermission("esani_pantportal", "qrbag"),
    ],
)
class QRBagAPI:  # type: ignore [call-arg]
    @route.get(
        "/{qr}",
        auth=JWTAuth(),
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
            user = self.context.request.user  # type: ignore
            branch = user.branch
            company_branch = branch if isinstance(branch, CompanyBranch) else None
            kiosk = branch if isinstance(branch, Kiosk) else None

            found = QRCodeGenerator.qr_code_exists(qr)

            if not found:
                return HttpResponseBadRequest(
                    json.dumps({"error": f"invalid QR code {qr}"})
                )

            return QRBag.objects.create(
                **{k: v for k, v in payload.dict().items() if k != "status"},
                qr=qr,
                owner=user,
                company_branch=company_branch,
                kiosk=kiosk,
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
            if attr != "status":
                setattr(item, attr, value)
            else:
                user = self.context.request.user  # type: ignore
                is_backbone_user = user.groups.filter(name="BackboneUsers").exists()
                if value == QRBag.STATE_VENDOR_REGISTERED:
                    item.increment_tour()
                elif value == QRBag.STATE_BACKBONE_COLLECTED:
                    if is_backbone_user:
                        item.set_backbone_collected()
                    else:
                        raise StatusChangeNotAllowed(value)
                else:
                    raise InvalidQRBagStatus(value)

        user = self.context.request.user  # type: ignore
        item.owner = user
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


class QRStatusOut(ModelSchema):
    class Config:
        model = QRStatus
        model_fields = [
            "code",
            "name_da",
            "name_kl",
        ]


@api_controller(
    "/qrstatus",
    tags=["QR-Status"],
    permissions=[
        permissions.AllowAny,
    ],
)
class QRStatusAPI:  # type: ignore [call-arg]
    @route.get("/", response=List[QRStatusOut])
    def list(self):
        return QRStatus.objects.all()
