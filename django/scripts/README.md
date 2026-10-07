# Tenant-scoped builder contract

The API is `/api/builder/`. An operator-created bearer grant is fixed to one
site, Discord guild, channel and user; expires in at most 30 days; is stored only
as a hash server-side; and becomes unusable after revocation or membership loss.
Read returns only that tenant's draft pages and asset metadata. Write accepts
only `{page_id?, title, html, version?, slug?}` and saves a draft. There is no
publish, shell, SQL, membership, billing or cross-tenant operation.

`connect_builder` provisions a protected 0600 client config file outside the
repo (never in chat or logs), validating the owner's actual Discord identity.
Its guild/channel binding cannot be reused for another site. Example shape:

```
python manage.py connect_builder --site example --owner discord_123 \
  --guild 456 --channel 789 --discord-user 123 \
  --output /absolute/private/location/example.json
```

The isolated agent's only data tools should wrap:

```
python scripts/builder_client.py read --config /absolute/private/location/example.json
python scripts/builder_client.py draft --config /absolute/private/location/example.json < draft.json
```

The host-owned wrapper pins the configuration path and trusted ingress context;
it must not accept either from model text or messages. Do **not** expose a generic
shell or this command with arbitrary arguments to users. One runtime/session and
credential per tenant/actor; separate workspaces and memory; no inherited general
agent tools, other tenant configs, database credentials or account-wide API keys.
A shared agent with all config files is **not isolated**, regardless of prompts.

The HTTP headers are claims from this trusted adapter, not proof of a Discord
message by themselves. The bearer is a narrow capability. Never expose it to
the model; the signed Discord endpoint verifies platform messages separately.

The adapter refuses redirects and non-HTTPS hosted origins. It reads only an
owner-only regular credential file, accepts draft JSON on stdin and never
prints credentials or raw transport exceptions. Server policy is authoritative.

## Direct Discord commands

`discord-command.json` describes `/site status` and `/site draft title text`.
An operator registers it with the intended existing Discord application and
sets its interaction endpoint to `/discord/interactions/`. **Do not replace an
existing interaction endpoint** without migrating its existing command handlers;
otherwise keep these handlers behind the existing bot's reviewed dispatcher.
No automatic registration is performed by these files.

The server verifies Ed25519 signatures, five-minute timestamp freshness, the
application ID, unique interaction ID, bound guild/channel and the actor's current
site membership. Replies are ephemeral with mentions disabled. `/site draft`
creates a plain-text draft, not an LLM-generated page. The isolated agent adapter
is the route for AI-assisted edits; its runtime is not provisioned by this PR.

Routine activation requires the approved, merged matching skill proposal and
verification of the target runtime's restricted toolset and real Discord routing.

## Restricted MCP runtime

Install `requirements-builder.txt` in the isolated worker and launch
`scripts/builder_mcp.py --config /operator/pinned/private/config.json` through the
host's tool configuration. MCP 2.x exposes exactly `read_site()` and
`draft_page(draft={title, html, page_id?, version?, slug?})`. Neither accepts a tenant,
URL, credential path or Discord identity. The host must expose **only these two
tools** to the tenant builder and use an isolated session/memory for each context.
Do not attach it to a privileged general-purpose session and call that isolated.
