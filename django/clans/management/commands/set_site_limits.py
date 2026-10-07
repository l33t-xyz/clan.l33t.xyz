from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from clans.models import AuditEvent, Site
from clans.services import usage


class Command(BaseCommand):
    help = "Operator-only plan allowance change; does not create a payment or subscription."

    def add_arguments(self, p):
        p.add_argument("site")
        p.add_argument("--plan", choices=["free", "plus"], required=True)
        p.add_argument("--pages", type=int, required=True)
        p.add_argument("--storage-mb", type=int, required=True)

    def handle(self, *args, **o):
        if not 1 <= o["pages"] <= 100 or not 1 <= o["storage_mb"] <= 2048:
            raise CommandError("Choose 1–100 pages and 1–2048 MB.")
        with transaction.atomic():
            s = Site.objects.select_for_update().get(slug=o["site"])
            if s.pages.count() > o["pages"] or usage(s) > o["storage_mb"] * 1024 * 1024:
                raise CommandError("Cannot lower limits below current usage.")
            s.plan = o["plan"]
            s.page_limit = o["pages"]
            s.storage_limit = o["storage_mb"] * 1024 * 1024
            s.save()
            AuditEvent.objects.create(
                site=s,
                action="plan.changed",
                detail=f"{s.plan}: {s.page_limit} pages, {o['storage_mb']} MB",
            )
        self.stdout.write("Plan allowances updated. No payment was processed.")
