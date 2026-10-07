# Clan studio (Django replacement)

A small Discord-first website builder: server-rendered pages, a rich-text editor,
MySQL content and media, draft/review/publish, and tenant-scoped builder access.
The original Next.js frontend in the repository root remains unchanged.

## Local development

Python 3.12+ and MySQL 8 are required. A dedicated, disposable local database is
intentional; never point tests at an existing hosted application database.

```
docker run -d --name clan-builder-mysql -p 127.0.0.1:53316:3306 \
  -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -e MYSQL_DATABASE=clan_builder mysql:8.0
uv venv --python 3.13 .venv
uv pip sync django/requirements.txt
.venv/bin/python django/manage.py migrate
.venv/bin/python django/manage.py collectstatic --noinput
.venv/bin/gunicorn --chdir django clan_project.wsgi --bind 127.0.0.1:18461
```

The passwordless database above is **only** a loopback-bound disposable test
container. Hosted configuration rejects root and empty passwords.

Local mode offers a “Try the editor” action that creates a new sample tenant and
session, capped at 30 sample users. Hosted modes never expose this action. Set
`CLAN_MODE=preview` or `production` and a unique protected runtime before serving
real users. A temporary local preview is not a production deployment.

## What works

- Discord OAuth through django-allauth, `identify` only, immutable subject IDs,
  state validation, no email linking or stored OAuth tokens.
- Three owner websites per identity; owner/editor roles; owner-only settings and
  membership; published pages are public, drafts are not.
- Locally vendored Quill 2.0.3 editor, image upload/library, four themes, public
  cover image, Discord invite, optional PayPal donation link.
- Independent live snapshots, explicit publication, optimistic edit conflicts,
  append-only revisions and draft restoration.
- MySQL LONGBLOB image storage. Uploads are decoded/re-encoded into WebP, strip
  metadata, reject invalid/oversized images, and enforce tenant ownership.
- Free allowances: provisional defaults of 5 pages / 25 MiB. Content accounting
  includes revisions with a small per-revision metadata allowance. These are
  application allowances, not a measurement of InnoDB disk usage. Operator-only
  limit changes are supported. No paid checkout or subscription is implemented.
- Scoped builder API plus signed Discord `/site status` and `/site draft`.
  Direct slash drafts are plain text. AI-generated drafts use the narrow client;
  the model itself and live bot routing are separate integration work.
- Offline Airtable/legacy export validation and draft-only import.

## Tests

```
.venv/bin/python django/manage.py test clans --noinput
```

Tests use `test_clan_builder`. This name must never be a production database.
The suite verifies isolation, optimistic concurrency, atomic quota races, real
OAuth callbacks with mocked Discord responses, signed interactions, media
privacy and safe imports. Browser acceptance is described in
`../docs/plans/django-builder/validation.md`.

## Importing old sites

`import_clan` accepts `{"records":[{"fields":{"title":"Story","slug":"story",
"content":"Old content","attachments":[]}}]}` from WebPages, or
`{"public_pages":[...]}` / `{"pages":[...]}` with the same fields.

```
.venv/bin/python django/manage.py import_clan export.json --site example --owner discord_123
# After reviewing the dry-run report:
.venv/bin/python django/manage.py import_clan export.json --site example --owner discord_123 --apply
```

New slugs only; all-or-nothing; quota checked; nothing published automatically.
Content is preserved as escaped text, **not** executed MDX or rendered Markdown.
This preserves source safely but requires formatting review in the visual editor.
Attachment URLs are counted and deferred, never fetched (no SSRF). Upload the
original image files separately. SiteMeta, member-only pages and attachment
migration require a reviewed mapping after exports are available; this command
is not a claim that complete Airtable migration has happened.

Existing clan addresses must be listed in `LEGACY_RESERVED_SLUGS` before opening
signups. They cannot be self-claimed. Assign their owners through a reviewed
operator migration after verifying identity and import authority.

## Hosting and bot integration

See `deploy/README.md` and `scripts/README.md`. Live OAuth, Discord command
registration, isolated bot runtime, wildcard TLS/DNS and deployment are explicit
operator steps, not activated by this repository or a branch push.

## Vendor provenance

Quill 2.0.3 JS/CSS and BSD-3-Clause license are vendored from its published npm
package via jsDelivr. Missing sourcemap references were removed; no runtime CDN
fetch is required. See `clans/static/clans/vendor/QUILL-LICENSE.txt`.
