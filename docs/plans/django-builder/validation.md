# Validation record

## Implemented and exercised

- 72 MySQL 8 tests pass, including real concurrent quota/edit races, cross-tenant
  route/object/media/revision access, draft/live separation, XSS stripping,
  malformed inputs, stale versions, revocation/expiry, membership loss, safe
  import and reserved legacy addresses.
- OAuth callback exercised through the real allauth flow with mocked Discord
  token/profile responses: identity-only scope, immutable user subject, state
  isolation and no OAuth-token persistence. Real provider login still requires
  the application's registered callback and credentials.
- Real MCP 2.3 stdio → scoped HTTP → MySQL integration passes. Exactly two tools;
  foreign page IDs cannot be edited; extra tenant/origin/config/publish fields
  are rejected; revoked connections cannot read; no publication occurs.
- Actual Chromium browser journey passes: create isolated sample, rich-text edit,
  image upload, save private draft, publish, change theme/cover, restore earlier
  draft without changing public content. Anonymous studio access redirects to
  login. Sixteen rendered pages at 1440 and 390 pixels have no horizontal
  overflow; zero JavaScript errors. Screenshots inspected locally.
- Django checks, migration-drift check, static collection, Ruff and diff check
  pass. Offline production settings have no `check --deploy` errors; HSTS
  include-subdomains/preload warnings are intentionally retained until all
  subdomains are verified HTTPS. This is not a hosted runtime acceptance test.
- Locked web and optional builder dependencies: pip-audit reports no known
  vulnerabilities at review time. This is a dependency advisory check, not an
  application penetration test.
- Workshop routine scan clean; zero configured evaluators. Complete v1 review
  artifact is pending and inactive under `docs/skill-proposals/`.

## Review-driven corrections

Reserved legacy addresses before signups; enforced tenant host routing; bounded
request bodies and image decoding; included revision overhead in storage
allowances; validated malformed owner-action IDs; restricted image formats;
made hosted settings fail closed; labelled editor toolbar controls; adopted the
installed MCP 2.x API and strict draft input model after protocol verification.

## Explicit boundaries

No live website, existing database, bot runtime, OAuth app, DNS, TLS or service
configuration was modified. The preview uses synthetic local tenants and a
separate MySQL instance. Existing Next.js source is preserved.

Not claimed: full Airtable migration (exports pending), live Discord OAuth,
real bot registration/context routing, hosted cutover, paid subscriptions,
operational monitoring/backup rollout, or independent reviewer approval.
The bot routine awaits human review/merge and activation in a genuinely isolated
runtime; a shared privileged agent is not made safe by these instructions.

## Reproduce

Install `django/requirements.txt`, `requirements-builder.txt` and
`requirements-browser.txt`; start the dedicated MySQL described in the Django
README; run migrations, tests and static collection. Start the local-mode
Gunicorn preview, install Chromium, then run `django/scripts/test_browser.py`.
The browser test creates synthetic sample tenants and is not for production.

## Gamer visual identity iteration

Replaced the cream/forest presentation with charcoal surfaces, electric violet,
neon accents, bold sans-serif headings, channel-style example navigation and a
geometric clan crest. Applied the identity to the landing page, studio, editor,
settings and public pages. Existing theme choices remain distinct accents on
the dark layout. No schema, account, authorization or publishing changes.

Re-ran the upload → draft → publish → cover/theme → restore browser journey
and all sixteen desktop/mobile route checks. No horizontal overflow or browser
JavaScript errors; desktop and mobile screenshots visually reviewed.
