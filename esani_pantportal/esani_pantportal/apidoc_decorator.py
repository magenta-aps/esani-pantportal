# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from ninja.main import NinjaAPI


def swagger_csp(view_func=None):
    # This gets called whenever django ninja wants to render docs
    # We hook into it by specifying docs_decorator in the NinjaExtraAPI constructor

    if (
        view_func.func.__module__ == "ninja.openapi.views"
        and view_func.func.__name__ == "openapi_view"
    ):
        # If the called function is the one that renders the swagger html
        def openapi_view_csp(request: HttpRequest, api: "NinjaAPI") -> HttpResponse:
            # Return a copy of the template that
            # has CSP attributes in the correct places
            view_tpl = "../templates/ninja/swagger_cdn_csp.html"
            context = {
                "api": api,
                "openapi_json_url": reverse(f"{api.urls_namespace}:openapi-json"),
            }
            return render(request, view_tpl, context)

        # Insert the replacement with a closure containing
        # the original function arguments
        return partial(
            openapi_view_csp,
            *view_func.args,
            **view_func.keywords,
        )

    else:
        return view_func
