import json
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from clans.models import DiscordBinding, Site
from clans.services import grant_token


class Command(BaseCommand):
    help = "Operator-only: bind Discord context and write a private builder credential file. Never prints the token."

    def add_arguments(self, p):
        for name in ["site", "owner", "guild", "channel", "discord-user", "output"]:
            p.add_argument("--" + name, required=True)
        p.add_argument("--days", type=int, default=7)

    def handle(self, *args, **o):
        if not 1 <= o["days"] <= 30:
            raise CommandError("Grant duration must be 1–30 days.")
        target = Path(o["output"]).expanduser()
        if not target.is_absolute() or target.exists():
            raise CommandError("Use a new absolute private output path.")
        base = urlparse(settings.PUBLIC_ORIGIN)
        if base.scheme != "https" and base.hostname not in {"localhost", "127.0.0.1"}:
            raise CommandError("Hosted builder requires HTTPS.")
        try:
            site = Site.objects.get(slug=o["site"])
            user = get_user_model().objects.get(username=o["owner"])
            with transaction.atomic():
                if (
                    DiscordBinding.objects.filter(
                        guild_id=o["guild"], channel_id=o["channel"]
                    )
                    .exclude(site=site)
                    .exists()
                ):
                    raise CommandError("Channel belongs to another website.")
                grant, token = grant_token(
                    site,
                    user,
                    o["guild"],
                    o["channel"],
                    o["discord_user"],
                    timezone.now() + timedelta(days=o["days"]),
                )
                DiscordBinding.objects.get_or_create(
                    site=site, guild_id=o["guild"], channel_id=o["channel"]
                )
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as f:
                    json.dump(
                        {
                            "origin": settings.PUBLIC_ORIGIN,
                            "site": site.slug,
                            "token": token,
                            "guild": o["guild"],
                            "channel": o["channel"],
                            "actor": o["discord_user"],
                        },
                        f,
                    )
        except CommandError:
            raise
        except Exception:
            raise CommandError(
                "Builder provisioning failed; no credential was printed. Inspect the private output path before retrying."
            )
        self.stdout.write(
            "Builder connection created. Private configuration written; keep it outside chat and version control."
        )
