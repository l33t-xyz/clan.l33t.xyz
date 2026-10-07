"""Offline, draft-only import. No URLs are fetched, and MDX is never evaluated."""

from html import escape

from django.core.exceptions import ValidationError
from django.db import transaction

from . import services
from .models import Site


def normalize_export(data):
    if isinstance(data, dict) and "records" in data:
        records = data["records"]
        if not isinstance(records, list):
            raise ValidationError("records must be a list.")
        rows = [r.get("fields", {}) for r in records if isinstance(r, dict)]
        if len(rows) != len(records):
            raise ValidationError("Every record must contain a fields object.")
    elif isinstance(data, dict) and "public_pages" in data:
        rows = data["public_pages"]
    elif isinstance(data, dict) and "pages" in data:
        rows = data["pages"]
    else:
        raise ValidationError("Expected records, public_pages or pages.")
    if not isinstance(rows, list) or not rows or len(rows) > 100:
        raise ValidationError("Import between 1 and 100 pages at a time.")
    normalized = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValidationError("Every page must be an object.")
        title = row.get("title")
        handle = row.get("slug")
        content = row.get("content", "")
        if not isinstance(title, str) or not title.strip() or len(title) > 120:
            raise ValidationError("Each page needs a title of 1–120 characters.")
        if not isinstance(handle, str):
            raise ValidationError("Each page needs a slug.")
        services.slug(handle, 64)
        if handle in seen:
            raise ValidationError("Duplicate slug in import.")
        seen.add(handle)
        if not isinstance(content, str) or len(content.encode()) > services.MAX_HTML:
            raise ValidationError("Content must be text smaller than 100 KB.")
        # Preserve all source as text, including MDX, until explicitly converted in the editor.
        # This cannot execute JSX/imports, remote scripts or attachment URLs.
        html = "<p>" + escape(content).replace("\n", "</p><p>") + "</p>"
        normalized.append(
            {
                "title": title.strip(),
                "slug": handle,
                "html": html,
                "attachment_count": len(row.get("attachments", []))
                if isinstance(row.get("attachments", []), list)
                else 0,
            }
        )
    return normalized


@transaction.atomic
def import_pages(site, user, data, apply=False):
    site = Site.objects.select_for_update().get(pk=site.pk)
    services.membership(site, user, owner=True)
    rows = normalize_export(data)
    if any(site.pages.filter(slug=r["slug"]).exists() for r in rows):
        raise ValidationError(
            "An imported address already exists. Nothing was overwritten."
        )
    if site.pages.count() + len(rows) > site.page_limit:
        raise ValidationError(
            "Import exceeds the page allowance. Adjust the operator limit before migration."
        )
    services.capacity(
        site,
        sum(2 * len(r["html"].encode()) + len(r["title"].encode()) + 256 for r in rows),
    )
    if apply:
        for r in rows:
            services.save_page(
                site,
                user,
                None,
                r["title"],
                r["html"],
                0,
                source="import",
                new_slug=r["slug"],
            )
    return {
        "pages": len(rows),
        "attachments_deferred": sum(r["attachment_count"] for r in rows),
        "applied": apply,
        "published": False,
    }
