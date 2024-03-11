# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

"""
Django settings for esani_pantportal project.

Generated by 'django-admin startproject' using Django 4.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from project.util import strtobool

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
VERSION = os.environ.get("COMMIT_TAG", "")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(strtobool(os.environ.get("DJANGO_DEBUG", "False")))
TESTING = bool(len(sys.argv) > 1 and sys.argv[1] == "test")

if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

ALLOWED_HOSTS = json.loads(os.environ.get("ALLOWED_HOSTS", "[]"))

if os.environ.get("CSRF_ORIGINS", False):
    CSRF_TRUSTED_ORIGINS = json.loads(os.environ.get("CSRF_ORIGINS", "[]"))


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "esani_pantportal",
    "barcode_scanner",
    "ninja_extra",
    "ninja_jwt",
    "django_bootstrap_icons",
    "betterforms",
    "debug_toolbar",
    "template_profiler_panel",
    "simple_history",
    "phonenumber_field",
    "captcha",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    # "anymail",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django_mitid_auth.middleware.LoginManager",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django_cprofile_middleware.middleware.ProfilerMiddleware",  # Active when DEBUG=True
]

ROOT_URLCONF = "project.urls"
APPEND_SLASH = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "esani_pantportal.context_processors.environment",
            ],
        },
    },
]

WSGI_APPLICATION = "esani_pantportal.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "default_cache",
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
AUTH_USER_MODEL = "esani_pantportal.User"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "da-DK"
LANGUAGES = [
    ("da", "Dansk"),
    ("kl", "Kalaallisut"),
]
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]
LOCALE_MAP = {"da": "da-DK", "kl": "kl-GL"}

TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = "."
DECIMAL_SEPARATOR = ","


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "/static"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Email
# https://simpleisbetterthancomplex.com/tutorial/2017/05/27/how-to-configure-mailgun-to-send-emails-in-a-django-app.html
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.eu.mailgun.org")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("MAILGUN_SMTP_USERNAME", "pant@pant.gl")
EMAIL_HOST_PASSWORD = os.environ.get("MAILGUN_SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "pant@pant.gl")

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/produkt/"
LOGOUT_REDIRECT_URL = "/"

DEFAULT_CSV_HEADER_DICT = {
    "product_name": "Produktnavn [str]",
    "barcode": "Stregkode [str]",
    "material": "Materiale [str]",
    "height": "Højde [mm]",
    "diameter": "Diameter [mm]",
    "weight": "Vægt [g]",
    "capacity": "Volumen [ml]",
    "shape": "Form [str]",
    "danish": "Dansk pant [str]",
}

QR_URL_PREFIX = "http://pant.gl?QR="
QR_ID_LENGTH = 9  # Length of QR ID part, default 9 (one BILLION different codes)
QR_HASH_LENGTH = 8  # Length of QR control code, default 8

QR_GENERATOR_SERIES: dict[str, dict[str, str | int]] = {
    "small": {"name": "Små sække", "prefix": 0},
    "large": {"name": "Store sække", "prefix": 1},
    "test": {"name": "QR-koder til test", "prefix": 9},
}
QR_OUTPUT_DIR = "/srv/media/qr_codes"

DEFAULT_REFUND_VALUE = 200

TOMRA_SFTP_URL = os.environ.get(
    "TOMRA_SFTP_URL", "sftp://sftp_tomra:foo@pantportal-sftp:22/deposit_payouts/"
)
TOMRA_PATH = os.environ.get("TOMRA_PATH", "/srv/media/deposit_payouts/")
TOMRA_API_ENV = os.environ.get("TOMRA_API_ENV", "eu-sandbox")
TOMRA_API_KEY = os.environ.get("TOMRA_API_KEY", "")
TOMRA_API_CLIENT_ID = os.environ.get("TOMRA_API_CLIENT_ID", "")
TOMRA_API_CLIENT_SECRET = os.environ.get("TOMRA_API_CLIENT_SECRET", "")

# https://redmine.magenta.dk/issues/58865
MIN_BOTTLE_DIAMETER = int(os.environ.get("MIN_BOTTLE_DIAMETER", 50))
MAX_BOTTLE_DIAMETER = int(os.environ.get("MAX_BOTTLE_DIAMETER", 130))

MIN_BOTTLE_HEIGHT = int(os.environ.get("MIN_BOTTLE_HEIGHT", 85))
MAX_BOTTLE_HEIGHT = int(os.environ.get("MAX_BOTTLE_HEIGHT", 380))

MIN_BOTTLE_VOLUME = int(os.environ.get("MIN_BOTTLE_VOLUME", 150))
MAX_BOTTLE_VOLUME = int(os.environ.get("MAX_BOTTLE_VOLUME", 3000))

MIN_CAN_DIAMETER = int(os.environ.get("MIN_CAN_DIAMETER", 50))
MAX_CAN_DIAMETER = int(os.environ.get("MAX_CAN_DIAMETER", 100))

MIN_CAN_HEIGHT = int(os.environ.get("MIN_CAN_HEIGHT", 80))
MAX_CAN_HEIGHT = int(os.environ.get("MAX_CAN_HEIGHT", 200))

MIN_CAN_VOLUME = int(os.environ.get("MIN_CAN_VOLUME", 150))
MAX_CAN_VOLUME = int(os.environ.get("MAX_CAN_VOLUME", 1000))


MIN_DIAMETER = min(MIN_BOTTLE_DIAMETER, MIN_CAN_DIAMETER)
MIN_HEIGHT = min(MIN_BOTTLE_HEIGHT, MIN_CAN_HEIGHT)
MIN_VOLUME = min(MIN_BOTTLE_VOLUME, MIN_CAN_VOLUME)

MAX_DIAMETER = max(MAX_BOTTLE_DIAMETER, MAX_CAN_DIAMETER)
MAX_HEIGHT = max(MAX_BOTTLE_HEIGHT, MAX_CAN_HEIGHT)
MAX_VOLUME = max(MAX_BOTTLE_VOLUME, MAX_CAN_VOLUME)


PRODUCT_CONSTRAINTS: dict[str, dict[str, tuple]] = {
    "diameter": {
        "F": (MIN_BOTTLE_DIAMETER, MAX_BOTTLE_DIAMETER),
        "D": (MIN_CAN_DIAMETER, MAX_CAN_DIAMETER),
        "A": (MIN_DIAMETER, MAX_DIAMETER),
    },
    "height": {
        "F": (MIN_BOTTLE_HEIGHT, MAX_BOTTLE_HEIGHT),
        "D": (MIN_CAN_HEIGHT, MAX_CAN_HEIGHT),
        "A": (MIN_HEIGHT, MAX_HEIGHT),
    },
    "capacity": {
        "F": (MIN_BOTTLE_VOLUME, MAX_BOTTLE_VOLUME),
        "D": (MIN_CAN_VOLUME, MAX_CAN_VOLUME),
        "A": (MIN_VOLUME, MAX_VOLUME),
    },
}

DATE_FORMAT = "j. N Y"

if DEBUG:
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]

CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.math_challenge"
CAPTCHA_LETTER_ROTATION = None
CAPTCHA_NOISE_FUNCTIONS = ("captcha.helpers.noise_dots",)
CAPTCHA_MATH_CHALLENGE_OPERATOR = "x"
CAPTCHA_FONT_SIZE = 33

# When set to True, the string “PASSED” (any case) will be accepted as a valid response to any CAPTCHA. Use this for testing purposes.
CAPTCHA_TEST_MODE = TESTING

if TESTING:
    import logging

    logging.disable(logging.CRITICAL)

TWO_FACTOR_LOGIN_TIMEOUT = 0  # Never timeout
TWO_FACTOR_REMEMBER_COOKIE_AGE = 30 * 24 * 60 * 60  # Re-authenticate once per month
BYPASS_2FA = bool(strtobool(os.environ.get("BYPASS_2FA", "False")))
DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False


DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "template_profiler_panel.panels.template.TemplateProfilerPanel",
]

# Logging

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "gunicorn": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["gunicorn"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["gunicorn"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

log_filename = "/var/log/pantportal.log"
if os.path.isfile(log_filename) and ENVIRONMENT != "development":
    LOGGING["handlers"]["file"] = {
        "class": "logging.FileHandler",  # eller WatchedFileHandler
        "filename": log_filename,
        "formatter": "simple",
    }
    LOGGING["root"] = {
        "handlers": ["gunicorn", "file"],
        "level": "INFO",
    }
    LOGGING["loggers"]["django"]["handlers"].append("file")
