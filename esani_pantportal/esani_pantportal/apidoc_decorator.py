# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import re

from django.http import HttpRequest, HttpResponse


def swagger_csp(view_func=None):
    # This gets called whenever django ninja wants to render docs
    # We hook into it by specifying docs_decorator in the NinjaExtraAPI constructor

    if (
        view_func.func.__module__ == "ninja.openapi.views"
        and view_func.func.__name__ in ("openapi_view", "openapi_view_cdn")
    ):
        # If the called function is the one that renders the swagger html
        def apply_nonce(request: HttpRequest) -> HttpResponse:
            # Update the response content to include nonces
            response = view_func(request)
            nonce = request.csp_nonce  # type: ignore
            content = response.content.decode("utf-8")
            content = re.sub("<script", f'<script nonce="{nonce}"', content)
            content = re.sub("<link", f'<link nonce="{nonce}"', content)
            response.content = content.encode("utf-8")
            return response

        return apply_nonce
    else:
        return view_func
