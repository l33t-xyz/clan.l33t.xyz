# Hosted rollout (review-only)

1. Choose a **new preview hostname and serving path**, a dedicated MySQL database
   and least-privilege account. Do not reuse or modify the legacy app/database.
   Confirm the selected loopback port is unused immediately before activation.
2. Install the reviewed commit and locked Python dependencies under the checkout
   owner. Provision the protected runtime using the host's credential mechanism.
   The provided runtime shape contains no credentials. Use a 50+ character random
   Django signing key, a non-root database user/password, exact hosts, canonical
   HTTPS origin and the preview mode. Keep secrets outside the repository.
3. Set `CLAN_RUNTIME_FILE` to the checkout-owner credential file, readable by the
   serving UID, not world-readable or group-writable. The host follows the
   existing Django checkout-owner credential and shared-log-directory pattern.
4. Register Discord OAuth callback `<PUBLIC_ORIGIN>/accounts/discord/login/callback/`.
   Use the matching application client ID/secret. Only `identify` is requested.
   Exercise a real sign-in, sign-out and returning-user flow before opening access.
5. Verify TLS certificate/key exist, match and cover the real hostname. Create
   shared log parents and confirm serving UID access before adding a vhost or
   Supervisor process. Templates are examples, not active configuration.
6. Back up any nonempty target DB, then run migrate, collectstatic, check and
   `check --deploy` using the hosted runtime. Production must use HTTPS cookies,
   exact allowed hosts, no local demo action, and a trusted proxy that overwrites
   X-Forwarded-Proto. Do not share session cookies across tenant subdomains.
7. Install only the new application's reviewed config. Run actual Apache and
   Supervisor parser checks before targeted reload/update. Never restart shared
   services blindly or enable unrelated configuration. `autostart=false` is a
   safe template default, not an invented application activation flag.
8. Verify health, real Discord login, create/edit/upload/preview/publish, two-user
   isolation, missing-page 404, media privacy, mobile UI and absence of secrets
   in logs. Do not log OAuth query strings or Authorization headers.
9. For the canonical site cutover, first inventory existing clan addresses and
   reserve them; map existing ownership, content and URLs; verify wildcard TLS
   and preserve rollback routing. Keep the old site available until acceptance.
10. Rollback is routing back to the unchanged legacy service and stopping only
    the new application process. Do not drop databases or delete imported data.

Allauth ships conditional unique constraints for email addresses that MySQL
cannot enforce. This application does not use email signup or email-based
account linking; Discord provider+subject is its identity boundary. The warning
is documented, not suppressed. Revisit before introducing email authentication.

Billing/checkout, operational monitoring/backups, real OAuth/bot connection and
legacy imports must be explicitly verified before calling this production-ready.

For staged main-site cutover, GitHub Pages retirement, and per-clan content
migration, see the [migration plan](../../docs/plans/django-builder/migration.md).
