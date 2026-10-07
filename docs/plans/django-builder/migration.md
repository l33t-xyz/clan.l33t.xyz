# Migration plan: replace the landing page, then migrate existing clans

Status: proposed rollout sequence. No routing, hosting, content, bot or OAuth
changes are performed by this document. Implementation review is PR #1.

## Decision and scope

Separate two releases:

1. Replace the basic GitHub Pages landing page at `clan.l33t.xyz` with the Django
   website studio. Existing clan subdomains keep their current hosting.
2. Migrate existing clans individually, preserving their public hostnames and
   reviewed content. Retire the legacy frontend/API dependency only after the
   last dependent clan has moved.

This avoids making the main-site launch wait for all content exports, and avoids
making a landing-page cutover unexpectedly switch established communities.
Keep the repository, history and useful wiki documentation. Retiring GitHub
Pages hosting does not mean deleting the repository or the legacy source.

## Evidence and inventory

- The canonical root currently serves the basic repository-derived landing page.
  GitHub Pages is configured from `master` at `/`, with the canonical custom domain.
- The [public clan directory](https://github.com/l33t-xyz/clan.l33t.xyz/wiki/Clans)
  lists established clan subdomains. Treat this as a starting list, not a complete
  DNS, owner or content inventory. The legacy README describes the separate
  Vercel/Airtable stack used by those sites.
- Legacy source renders a collection of tabs from `public_pages`, uses the first
  attachment as each page's cover and evaluates MDX. A members tab has separate
  session-aware behavior. The replacement must not assume these are all ordinary
  public rich-text pages or invent a legacy path structure from tab names.
- Current import is source-preserving, draft-only and offline. It does **not**
  convert MDX/Markdown, fetch attachments, map site metadata or preserve private
  member functionality. Tests of this importer are not full migration acceptance.

Before any cutover, record exact DNS origin/proxy/TTL settings, hostnames,
certificates, redirects, serving revisions and owner identities in private
operator records. Back up source exports and original attachments there too;
never commit real member data, credentials or private exports here.

## Release A — main site and controlled beta

### A1. Finish the launch prerequisites

- Review and merge the approved implementation; deploy the exact reviewed source
  to an independent persistent preview with its own database/runtime.
- Complete [hosted acceptance](../../../django/deploy/README.md): real Discord
  login, logout and returning-user identity; create/edit/upload/preview/publish;
  two-user isolation; valid HTTPS; no local demo action in hosted mode.
- Reserve **all** established clan handles before enabling creation. The code's
  current default reservation of one handle is not a complete inventory.
- Start with a small, explicitly provisioned beta. Add a server-enforced allowlist
  or invitation gate before advertising restricted onboarding; the current
  create-site view is not invitation-only. Keep the new-site creation gate closed
  until ownership reservations and hosted acceptance pass.
- Use central-host-only sign-in and cookies, explicit permitted hosts and trusted
  HTTPS proxy configuration. Exclude authenticated/editor/API routes from CDN
  caching. Validate public-cache invalidation on publication and unpublication.
- Verify database backups include image blobs and demonstrate a restore into a
  disposable database. Add basic uptime/error visibility and an operator contact.
- Confirm root-site links and onboarding copy accurately distinguish active
  features from a not-yet-connected bot. Billing and donations are not launch
  blockers; do not advertise an implemented paid subscription.

Exit: a persistent preview with a real owner account can complete the full
workflow, and the recovered database also serves its pages and images.

### A2. Switch only the main hostname

- Capture previous routing and a legacy source revision for rollback. Confirm
  whether the DNS provider proxies the origin; public DNS alone may hide it.
- Prepare the destination vhost and certificate for `clan.l33t.xyz`, configure
  the canonical production origin and register its exact Discord callback.
- With explicit cutover approval, switch only the main hostname to the new
  origin. Leave existing tenant records, wildcard records and unrelated domain
  records untouched. Purge only stale main-site cache entries as necessary.
- Verify from outside the host: canonical HTTPS, login callback, account return,
  editor, image delivery, publish/unpublish and useful 404s. Confirm the existing
  tenant hostnames still route to their prior services.
- Use a recommended 72-hour observation window, covering prior DNS/cache TTLs,
  before retiring the old Pages deployment. This is an operational acceptance
  window, not a promise that DNS always takes 72 hours.

Exit: the main domain serves Django reliably; existing clans are unaffected.

### A3. Retire the basic GitHub Pages deployment

Only after main-domain acceptance and propagation:

1. Confirm no relevant DNS records still target GitHub Pages.
2. Disable branch-based Pages publishing by setting its source to **None**.
   Unpublishing a deployment alone is insufficient because another source-branch
   commit can republish it. See [GitHub's source-change procedure](https://docs.github.com/en/pages/getting-started-with-github-pages/deleting-a-github-pages-site)
   and [unpublish behavior](https://docs.github.com/en/pages/getting-started-with-github-pages/unpublishing-a-github-pages-site).
3. Remove the obsolete Pages custom-domain binding and root `CNAME` through a
   reviewed cleanup after the routing switch, not before. Retain any independent
   domain-verification record unless its removal is separately needed.
4. Replace legacy onboarding instructions with the new editor/Discord workflow;
   label historical Airtable/Next.js instructions accordingly. Preserve the wiki
   and repository. Record what will happen to any discovered `github.io` links;
   disabling Pages does not itself provide redirects for that old hostname.
5. Verify the canonical root still works and a subsequent normal source update
   cannot accidentally restore the old Pages deployment.

Do not disable Vercel or the old content API in this step: established clans may
still depend on them.

### DNS inventory refinement

The existing tenant subdomains currently inherit a DNS-only Vercel CNAME at
`*.clan.l33t.xyz`; the listed clans do not have individual DNS records. Keep that
wildcard unchanged when switching the main domain. Use `/s/<handle>/` on the
main site during controlled onboarding, or separately provision approved exact
hostnames for new sites. Move each established clan using an exact DNS record
only after its import passes acceptance. Switch the wildcard last, once all
remaining consumers are ready, or explicitly pin every unmigrated consumer to
its old origin first. Reserve the infrastructure hostname `preview` as well.

## Release B — migrate existing clans one at a time

### B1. Build the reviewed migration manifest

For each clan, collect site metadata, ordered pages, stable source record IDs,
slugs, public/private classification, original attachment files and checksums,
current links/anchors, theme/cover mappings and verified Discord owner subjects.
Export source data; a cached public crawl is supporting evidence, not an
up-to-date or complete substitute for the source export.

Resolve these implementation gaps before importing live content:

- Safe Markdown-to-editor conversion and an explicit mapping for any MDX widgets;
  never execute imported JSX. Preserve code blocks, whitespace and game-specific
  text. Flag unsupported formatting for manual review.
- Asset import into MySQL with same-tenant link rewriting, duplicate detection,
  original-file retention and a report for files exceeding format/size limits.
  Preserve per-page covers as reviewed inline images or extend the model; do not
  silently collapse all page covers into one site image.
- Explicit, repeatable source-to-target IDs and dry-run reconciliation reports.
  Do not blindly rerun imports or overwrite later editor changes.
- Explicit handling of the seeded `home` page: the current importer rejects a
  slug already present. Import into a reviewed empty tenant or migrate the pristine
  starter page intentionally; never silently delete a user-edited page.
- Preserve page ordering and select the correct home page. Verify actual legacy
  URLs/anchors; add redirects or a compatibility page only where needed. URL
  fragments are not sent to the server, so hash-only navigation requires browser
  compatibility handling, not a server redirect rule alone.
- Keep private/member-only source data outside published pages. Public migration
  can proceed with private material withheld and explicitly recorded. Full private
  member-area parity requires additional reader authorization, not editor roles.
- Set transitional per-clan allowances to fit existing pages, assets and revision
  overhead. Do not truncate a legacy site to the five-page free default or require
  payment just to preserve existing content. Commercial terms remain undecided.

### B2. Pilot one established clan

- Have the verified owner log in with Discord, then assign the reserved tenant;
  no self-service claiming of established names.
- Dry-run import, reconcile counts/checksums/links/visibility and render previews.
  Review every page and image with the owner before publishing.
- Freeze legacy edits briefly; take a final export/diff and reconcile it. Avoid
  simultaneous editing of the same clan in both systems.
- Prepare the exact tenant hostname certificate and host routing. A certificate
  for `*.l33t.xyz` does not cover `name.clan.l33t.xyz`; verify coverage for the
  actual host or `*.clan.l33t.xyz` plus the main hostname separately.
- Publish approved pages and move only that tenant's DNS/routing with explicit
  cutover authority. Verify its home, navigation, media, old links, privacy and
  mobile presentation on the real hostname.
- Observe the pilot before repeating for the next clan. Keep unmigrated tenants
  on their existing services and retain all source backups.

### B3. Connect the builder and retire remaining legacy dependencies

Provision one isolated, tenant-scoped builder pilot after the website flow is
stable. Verify real guild/channel/user routing, current membership, revocation,
draft-only permissions and cross-tenant refusal. The existing bot endpoint must
not be replaced blindly. Review/merge/activation of the pending routine remains
separate from merely having an MCP adapter in source.

After all dependent clans pass migration acceptance, retire unused legacy
frontend/API integrations and old table-service access individually. Confirm
shared services have no unrelated consumers. Keep exports and source history;
no database, account or repository deletion is implied by deprecation.

## Rollback without losing new work

Before cutover, retain origin records, configs, source revisions and database
snapshots. On a failed cutover, route the affected hostname back only if the
legacy service is actually healthy. Preserve the new database and uploaded
assets; never restore an old snapshot over newer edits. If writes occurred,
freeze editing and reconcile/export them before reopening legacy editing. If the
legacy service was already broken, use a pre-reviewed static fallback or hold
page instead of calling a return to that broken origin a successful rollback.

## Next milestone

An independently hosted preview with real Discord sign-in and verified restore,
followed by approval of the **main-domain-only** cutover. Existing-clan migration
waits for reviewed exports and ownership mapping; billing is a later release.
