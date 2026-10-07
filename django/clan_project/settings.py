import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .runtime import load_runtime

RUNTIME = load_runtime()
BASE_DIR = Path(__file__).resolve().parent.parent
MODE = os.environ.get("CLAN_MODE", "local")
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if MODE in {"local", "test"}:
        SECRET_KEY = "local-test-only-not-a-hosted-secret"
    else:
        raise ImproperlyConfigured("A hosted instance needs DJANGO_SECRET_KEY.")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
CSRF_TRUSTED_ORIGINS = list(
    filter(None, os.getenv("CSRF_TRUSTED_ORIGINS", "").split(","))
)
PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "http://localhost:18461").rstrip("/")
CLAN_BASE_DOMAIN = os.getenv("CLAN_BASE_DOMAIN", "")
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.discord",
    "clans",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "clans.middleware.ResponsePolicy",
]
ROOT_URLCONF = "clan_project.urls"
WSGI_APPLICATION = "clan_project.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "clans.context.site_context",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "clan_builder"),
        "USER": os.getenv("MYSQL_USER", "root"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "53316"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/studio/"
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_ADAPTER = "clans.auth.DiscordAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "discord": {
        "SCOPE": ["identify"],
        "APP": {
            "client_id": os.getenv("DISCORD_CLIENT_ID", ""),
            "secret": os.getenv("DISCORD_CLIENT_SECRET", ""),
            "key": "",
        },
    }
}
DISCORD_READY = bool(
    os.getenv("DISCORD_CLIENT_ID") and os.getenv("DISCORD_CLIENT_SECRET")
)
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_CLIENT_ID", "")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = MODE not in {"local", "test"}
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT = SESSION_COOKIE_SECURE
SECURE_HSTS_SECONDS = 31536000 if MODE == "production" else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
# Only enable behind a proxy that overwrites this header.
if os.getenv("TRUST_PROXY_HTTPS") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Keep existing sites unclaimable until verified migration/ownership assignment.
LEGACY_RESERVED_SLUGS = set(
    filter(None, os.getenv("LEGACY_RESERVED_SLUGS", "amazon").split(","))
)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        }
    },
}

if MODE not in {"local", "test", "preview", "production"}:
    raise ImproperlyConfigured("Unknown CLAN_MODE.")
if MODE in {"preview", "production"}:
    from urllib.parse import urlparse

    if (
        len(SECRET_KEY) < 50
        or DATABASES["default"]["USER"] == "root"
        or not DATABASES["default"]["PASSWORD"]
        or "*" in ALLOWED_HOSTS
        or urlparse(PUBLIC_ORIGIN).scheme != "https"
        or PUBLIC_ORIGIN not in CSRF_TRUSTED_ORIGINS
    ):
        raise ImproperlyConfigured(
            "Hosted mode requires a strong key, restricted database credentials, explicit hosts and trusted HTTPS origin."
        )
