# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from typing import Optional

from ninja import FilterSchema, ModelSchema, Query
from ninja_extra import api_controller, permissions, route
from ninja_extra.pagination import paginate
from ninja_extra.schemas import NinjaPaginationResponseSchema

from esani_pantportal.models import Product


class ApprovedProductsOut(ModelSchema):
    class Config:
        model = Product
        model_fields = [
            "product_name",
            "barcode",
            "tax_group",
            "product_type",
        ]


class ApprovedProductsFilterSchema(FilterSchema):
    product_name: Optional[str]
    barcode: Optional[int]
    tax_group: Optional[int]
    product_type: Optional[str]


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
        qs.order_by("tax_group", "product_name", "barcode")

        return list(qs)
