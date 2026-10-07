# Spec
Add an independent Django application under django/, preserving all legacy source. Server-rendered templates plus a locally served Quill editor. MySQL is the only database. Discord OAuth via django-allauth; no password signups or email-based identity linking. Owners manage settings and members; owners/editors draft and publish.

Every page, blob, revision and builder grant belongs to a site. Services lock the site row before quota-sensitive changes and use expected-version checks for draft/publish/restore. Draft and published snapshots are separate. HTML is sanitized server-side and image references resolve only inside the same tenant. Public assets must be referenced by published content or the public hero.

Bot HTTP access uses expiring hashed per-tenant grants with fixed guild/channel/actor binding; no tenant enumeration or publication permission. Signed Discord slash interactions provide bounded direct draft/status operations and require current membership. Never give a shared general-purpose agent server/database credentials. Natural-language model execution is separate from authority.

Free limits default provisionally to 5 pages/25MiB, configurable by operator. No checkout, billing or automatic paid entitlement. Optional PayPal-only donation URL. Airtable imports accept an offline normalized export, dry-run by default, draft-only, no network asset downloads or MDX execution.

Rollback: stop new process; original site/code/database are unchanged. Hosted activation requires reviewed exact revision, dedicated DB/account, real OAuth callback, TLS and service configuration.
