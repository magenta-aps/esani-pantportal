# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

"""
URL configuration for esani_pantportal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from project.admin import pantadmin
from project.api import api
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path("admin/", pantadmin.urls),
    path("django-admin/", admin.site.urls),
    path("", include("esani_pantportal.urls", namespace="pant")),
    path("barcode/", include("barcode_scanner.urls", namespace="barcode")),
    path("api/", api.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path(
        "bruger/adgangskode/nulstil",
        auth_views.PasswordResetView.as_view(
            template_name="esani_pantportal/user/password/reset_begin.html",
        ),
        name="password_reset",
    ),
    path(
        "bruger/adgangskode/nulstil/sendt",
        auth_views.PasswordResetDoneView.as_view(
            template_name="esani_pantportal/user/password/reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "bruger/adgangskode/nulstil/<uidb64>/<token>",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="esani_pantportal/user/password/reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "bruger/adgangskode/nulstil/komplet",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="esani_pantportal/user/password/reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("captcha/", include("captcha.urls")),
    path("", include(tf_urls)),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
