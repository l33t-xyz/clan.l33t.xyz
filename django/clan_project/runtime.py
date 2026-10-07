"""Load a protected checkout-owner runtime file without echoing credential source."""

import os
import runpy
import stat
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def load_runtime():
    path = os.getenv("CLAN_RUNTIME_FILE")
    if not path:
        return {}
    try:
        p = Path(path)
        if (
            not p.is_absolute()
            or p.is_symlink()
            or p.stat().st_mode & (stat.S_IWGRP | stat.S_IRWXO)
        ):
            raise ValueError
        data = runpy.run_path(str(p))
        names = [
            "CLAN_MODE",
            "DJANGO_SECRET_KEY",
            "MYSQL_DATABASE",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
            "MYSQL_HOST",
            "MYSQL_PORT",
            "ALLOWED_HOSTS",
            "CSRF_TRUSTED_ORIGINS",
            "PUBLIC_ORIGIN",
            "CLAN_BASE_DOMAIN",
            "DISCORD_CLIENT_ID",
            "DISCORD_CLIENT_SECRET",
            "DISCORD_PUBLIC_KEY",
            "TRUST_PROXY_HTTPS",
            "LEGACY_RESERVED_SLUGS",
        ]
        values = {k: str(data[k]) for k in names if k in data}
        if (
            values.get("CLAN_MODE") not in {"preview", "production"}
            or len(values.get("DJANGO_SECRET_KEY", "")) < 50
            or not values.get("MYSQL_PASSWORD")
        ):
            raise ValueError
        if values.get("MYSQL_USER") == "root":
            raise ValueError
        for k, v in values.items():
            os.environ[k] = v
        return values
    except Exception:
        raise ImproperlyConfigured(
            "Hosted runtime is missing, insecure or invalid; inspect its protected file outside application logs."
        ) from None
