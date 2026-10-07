import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from clans.importing import import_pages
from clans.models import Site


class Command(BaseCommand):
    help = "Validate an offline page export. --apply imports new drafts only; never overwrites or publishes."

    def add_arguments(self, p):
        p.add_argument("file")
        p.add_argument("--site", required=True)
        p.add_argument("--owner", required=True)
        p.add_argument("--apply", action="store_true")

    def handle(self, *args, **o):
        try:
            path = Path(o["file"])
            if path.stat().st_size > 10 * 1024 * 1024:
                raise CommandError("Export is too large.")
            report = import_pages(
                Site.objects.get(slug=o["site"]),
                get_user_model().objects.get(username=o["owner"]),
                json.loads(path.read_text()),
                o["apply"],
            )
        except (
            OSError,
            ValueError,
            ValidationError,
            PermissionDenied,
            Site.DoesNotExist,
            get_user_model().DoesNotExist,
        ) as e:
            raise CommandError("Import rejected: " + str(e))
        self.stdout.write(json.dumps(report))
