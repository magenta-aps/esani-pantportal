# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import base64
from decimal import Decimal
from typing import Dict, List, Union

import orjson
from django.core.files import File
from ninja.renderers import BaseRenderer


class ORJSONRenderer(BaseRenderer):
    media_type = "application/json"

    @staticmethod
    def default(o):
        if type(o) is Decimal:
            return str(o)
        if isinstance(o, File):
            with o.open("rb") as file:
                return base64.b64encode(file.read()).decode("utf-8")
        raise TypeError

    def render(self, request, data, *, response_status):
        return self.dumps(data)

    def dumps(self, data):
        return orjson.dumps(data, default=self.default)


def json_dump(data: Union[Dict, List]):
    return ORJSONRenderer().dumps(data)
