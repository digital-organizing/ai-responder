"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.2.9.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

import environ

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = env("SECRET_KEY", default="secret")

DEBUG = env("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_HOSTS", default=[])

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)

ADMINS = [x.split(":") for x in env.list("DJANGO_ADMINS", default=[])]

# Application definition

INSTALLED_APPS = [
    "baton",
    "corsheaders",
    "django_bootstrap5",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "context",
    "chat",
    "crawler",
    "django_celery_results",
    "django_celery_beat",
    "baton.autodiscover",
    "django_json_widget",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "builtins": ["django.templatetags.i18n"],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.sentry_dsn",
                "core.context_processors.posthog_config",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite"),
}

CACHES = {
    "default": env.cache(default="dummycache://"),
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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="de-ch")


def _gettext(s: str) -> str:
    return s


LANGUAGES = (("de-ch", _gettext("German")), ("fr-ch", _gettext("French")))

TIME_ZONE = env.str("TIME_ZONE", default="UTC")

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/


STATIC_URL = "static/"
STATIC_ROOT = "/static"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_CONFIG = env.email_url("EMAIL_URL", default="smtp://user@:password@localhost:25")

vars().update(EMAIL_CONFIG)

EMAIL_USE_SSL = True
EMAIL_USE_TLS = False


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True


CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='redis')}:6379"
REDIS_URL = CELERY_BROKER_URL

CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ]
}


DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", default="")
AWS_S3_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", default="")

AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env("S3_REGION_NAME", default="")
AWS_S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default="")

AWS_S3_CUSTOM_DOMAIN = env("S3_CUSTOM_DOMAIN", default="")

AWS_QUERYSTRING_AUTH = False

QDRANT_HOST = env("QDRANT_HOST", default="qdrant")
QDRANT_PORT = env.int("QDRANT_PORT", default=6333)

OPENAI_KEY = env("OPENAI_KEY", default="")

INFOMANIAK_KEY = env("INFOMANIAK_KEY", default="")


BATON = {
    "SITE_HEADER": "AI Collab",
    "SITE_TITLE": "AI Toolbox",
    "INDEX_TITLE": "Site administration",
    "SUPPORT_HREF": "",
    "COPYRIGHT": "digital/organizing GmbH",  # noqa
    "POWERED_BY": "digital/organizing GmbH",
    "CONFIRM_UNSAVED_CHANGES": True,
    "SHOW_MULTIPART_UPLOADING": True,
    "ENABLE_IMAGES_PREVIEW": True,
    "CHANGELIST_FILTERS_IN_MODAL": True,
    "CHANGELIST_FILTERS_ALWAYS_OPEN": False,
    "CHANGELIST_FILTERS_FORM": True,
    "COLLAPSABLE_USER_AREA": False,
    "MENU_ALWAYS_COLLAPSED": False,
    "MENU_TITLE": "Menu",
    "MESSAGES_TOASTS": False,
    "GRAVATAR_DEFAULT_IMG": "retro",
    "GRAVATAR_ENABLED": True,
    "FORCE_THEME": None,
    "LOGIN_SPLASH": "/static/core/img/login-splash.png",
    "SEARCH_FIELD": {
        "label": "Search contents...",
        "url": "/search/",
    },
    "MENU": (
        {
            "type": "app",
            "name": "auth",
            "label": "Authentication",
            "icon": "fa fa-lock",
            "default_open": True,
            "models": (
                {"name": "user", "label": "Users"},
                {"name": "group", "label": "Groups"},
            ),
        },
        {
            "type": "app",
            "name": "chat",
            "label": "Chat",
            "icon": "fa fa-comments",
            "default_open": False,
            "models": (
                {"name": "chatbot", "label": "Bots"},
                {"name": "thread", "label": "Threads"},
            ),
        },
        {
            "type": "app",
            "name": "context",
            "label": "Context",
            "icon": "fa fa-book",
            "default_open": False,
            "models": (
                {"name": "collection", "label": "Collection", "icon": "fa fa-book"},
                {"name": "document", "label": "Document", "icon": "fa fa-document"},
            ),
        },
        {
            "type": "app",
            "name": "crawler",
            "label": "Crawl",
            "icon": "fa fa-globe",
            "default_open": False,
            "models": (
                {"name": "crawlconfig", "label": "Config", "icon": "fa fa-gear"},
                {"name": "page", "label": "Page", "icon": "fa fa-file-lines"},
            ),
        },
    ),
}


SELENIUM_URL = "http://selenium-hub:4444"

LOGIN_REDIRECT_URL = "/"


POSTHOG_KEY = env("POSTHOG_KEY", default="")
POSTHOG_HOST = env("POSTHOG_HOST", default="https://eu.i.posthog.com")

import sentry_sdk

SENTRY_DSN = env("SENTRY_DSN", default="")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=0.1,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=0.1,
)
