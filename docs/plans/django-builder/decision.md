# Decision: small Django studio, not a general-purpose app builder

## Context
The legacy frontend delegates page content to an external table service and a
separate API. The requested successor emphasizes approachable editing, Discord
identity and reliable tenant ownership with a small self-hosted footprint.

## Options
1. Keep the existing frontend and replace only its content API: less visual
   migration, but retains two application stacks and introduces another editor.
2. Add a server-rendered Django studio/public site with a focused rich-text
   editor: one primary application, direct permission enforcement, straightforward
   publishing and database operations.
3. Build a generic application-generation platform: much larger scope and a
   poor fit for simple community websites.

## Decision
Implement option 2 alongside the untouched legacy source. Use MySQL for data
and image blobs; Quill for rich text; Django/allauth for identity and sessions.
Keep AI drafts behind a two-tool tenant connection with human publication.
Preserve a future general website-builder boundary, without adding generic
platform abstractions now.

## Follow-through
Review and approve the implementation; provision isolated preview runtime;
verify real Discord login and builder routing; import old content from reviewed
exports; preserve old routing until a separately authorized cutover passes.
Size allowances are provisional operator settings, not pricing commitments.

## Rollout decision

Separate main landing-page replacement from established-clan migrations. Retire
GitHub Pages only after the main-domain cutover is verified; preserve the legacy
services until their last tenant moves. See the [migration plan](migration.md)
for evidence, launch gaps, acceptance gates and data-preserving rollback.
