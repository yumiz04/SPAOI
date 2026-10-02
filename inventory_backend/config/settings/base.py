from pathlib import Path
from datetime import date, timedelta

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    # terceros
    "rest_framework", "django_filters", "drf_spectacular", "rest_framework_simplejwt",
    # apps propias (se irÃ¡n agregando)
    "apps.core",
    "apps.products", "apps.inventory", "apps.sales", "apps.purchasing", "apps.lots",
    "apps.risk_config", "apps.analytics", "apps.alerts", "apps.forecasting",
    "apps.recommendations", "apps.dashboard", "apps.agent",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",      # antes de AuthenticationMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

STATIC_URL = "static/"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "inventory-risk-config",
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("DB_HOST"), "PORT": env("DB_PORT", default="5432"),
        "NAME": env("DB_NAME"), "USER": env("DB_USER"), "PASSWORD": env("DB_PASSWORD"),
        # Tablas de Django y modelos propios caen en inventory_agent; AW se referencia con esquema explÃ­cito.
        "OPTIONS": {"options": "-c search_path=inventory_agent,public"},
        "CONN_MAX_AGE": 60,
    }
}

_as_of = env("ANALYSIS_AS_OF_DATE", default="")
ANALYSIS_AS_OF_DATE = date.fromisoformat(_as_of) if _as_of else None

# Umbral (dias de cobertura) para generar la alerta AGOTAMIENTO_ESTIMADO (Paso 13).
DEPLETION_ALERT_THRESHOLD_DAYS = env.int("DEPLETION_ALERT_THRESHOLD_DAYS", default=7)

# Retencion de trazas del agente (Paso 19): purge_tool_logs borra las mas antiguas.
AGENT_TOOL_LOG_RETENTION_DAYS = env.int("AGENT_TOOL_LOG_RETENTION_DAYS", default=180)

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["apps.core.renderers.EnvelopeJSONRenderer"],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"agent": env("AGENT_THROTTLE_RATE", default="120/min")},
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=30), "REFRESH_TOKEN_LIFETIME": timedelta(days=1)}
SPECTACULAR_SETTINGS = {"TITLE": "Inventory Backend API", "VERSION": "1.0.0"}
