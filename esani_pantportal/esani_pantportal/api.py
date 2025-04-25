# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from django.db import IntegrityError
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from ninja import FilterSchema, ModelSchema, Query, Schema
from ninja_extra import ControllerBase, api_controller, permissions, route
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
    product_name: str | None
    barcode: int | None


@api_controller(
    "/produkter",
    tags=["Produkter"],
    permissions=[permissions.IsAuthenticatedOrReadOnly],
)
class ApprovedProductsAPI:  # type: ignore[call-arg]
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
        qs = filters.filter(Product.objects.filter(approved=True))  # type: ignore
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


class QRBagError(Schema):
    error: str


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
        else:
            return ""


class QRBagHistoryOut(QRBagOut):
    history_date: datetime


@api_controller(
    "/qrbag",
    tags=["QR-Pose"],
    permissions=[
        permissions.IsAuthenticatedOrReadOnly,
        DjangoPermission("esani_pantportal", "qrbag"),
    ],
)
class QRBagAPI:  # type: ignore[call-arg]
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
        response={
            201: QRBagOut,  # Meaning: a new QR bag was created
            400: QRBagError,
        },
    )
    def create(self, qr: str, payload: QRBagIn):
        try:
            user = self.context.request.user  # type: ignore
            branch = user.branch
            company_branch = branch if isinstance(branch, CompanyBranch) else None
            kiosk = branch if isinstance(branch, Kiosk) else None

            found = QRCodeGenerator.qr_code_exists(qr)

            if not found:
                return 400, QRBagError(error=f"invalid QR code {qr}")

            obj = QRBag.objects.create(
                qr=qr,
                owner=user,
                company_branch=company_branch,
                kiosk=kiosk,
                active=payload.active,  # type: ignore[attr-defined]
                status=payload.status,  # type: ignore[attr-defined]
            )
            return 201, obj  # signal that object was created
        except IntegrityError:
            return 400, QRBagError(error=f"qr {qr} already exists")

    @route.patch(
        "/{qr}",
        auth=JWTAuth(),
        url_name="qrbag_update",
        summary="Opdatér QR-pose",
        response={
            200: QRBagOut,  # Meaning: an existing QR bag was updated
            201: QRBagOut,  # Meaning: a new QR bag was created
            204: QRBagOut,  # Meaning: an existing QR bag was not updated (no changes)
            400: QRBagError,
        },
    )
    def update(self, qr: str, payload: QRBagIn):
        # Create QR bag if it does not exist
        try:
            item = QRBag.objects.get(qr=qr)
        except QRBag.DoesNotExist:
            return self.create(qr, payload)  # returns 201 or 400

        # Otherwise, update existing QR bag.
        # Track if QR bag is actually updated.
        changed: bool = False

        # Update "ordinary" QRBag attributes
        data = payload.dict(exclude_unset=True)
        for attr, new_value in data.items():
            old_value = getattr(item, attr, None)
            if new_value != old_value:
                changed = True
            setattr(item, attr, new_value)

        # Update QRBag "owner" attribute
        user = self.context.request.user  # type: ignore
        if user != item.owner:
            changed = True
        item.owner = user

        if changed:
            item.save()  # adds history item
            return 200, item
        else:
            return 204, item

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
class QRStatusAPI:  # type: ignore[call-arg]
    @route.get("/", response=list[QRStatusOut])
    def list(self):
        return QRStatus.objects.all()
