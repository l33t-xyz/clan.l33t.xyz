"""Narrow authority boundary. Never pass model text directly to an ORM or shell."""

import hashlib
import json
import time
from html import escape

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from . import services
from .models import BuilderGrant, DiscordBinding, InteractionReceipt, Page, Site


def error(message, status=403):
    return JsonResponse({"error": message}, status=status)


def payload(request):
    if request.content_type != "application/json":
        raise ValueError("JSON required")
    if len(request.body) > 110_000:
        raise ValueError("Request too large")
    body = json.loads(request.body)
    if not isinstance(body, dict):
        raise ValueError("Object required")
    return body


@csrf_exempt
@require_http_methods(["GET", "POST"])
def builder_api(request):
    """Token and trusted ingress context are fixed by operator, never model-selected."""
    raw = request.headers.get("Authorization", "")
    if not raw.startswith("Bearer ") or len(raw) > 256:
        return error("Invalid builder authorization")
    digest = hashlib.sha256(raw[7:].encode()).hexdigest()
    with transaction.atomic():
        grant = (
            BuilderGrant.objects.select_for_update()
            .select_related("site", "user")
            .filter(
                token_hash=digest,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if not grant:
            return error("Invalid builder authorization")
        # Match every context dimension; never accept a requested site ID.
        context = (
            request.headers.get("X-Discord-Guild"),
            request.headers.get("X-Discord-Channel"),
            request.headers.get("X-Discord-User"),
        )
        if context != (grant.guild_id, grant.channel_id, grant.discord_user_id):
            return error("This request is not bound to this builder")
        try:
            services.membership(grant.site, grant.user)
        except PermissionDenied:
            return error("Builder membership ended")
        if not SocialAccount.objects.filter(
            user=grant.user, provider="discord", uid=grant.discord_user_id
        ).exists():
            return error("Builder identity ended")
        if request.method == "GET":
            return JsonResponse(
                {
                    "site": {"name": grant.site.name, "slug": grant.site.slug},
                    "pages": [
                        {
                            "id": str(p.pk),
                            "title": p.title,
                            "slug": p.slug,
                            "html": p.draft_html,
                            "version": p.version,
                        }
                        for p in grant.site.pages.all()
                    ],
                    "assets": [
                        {"id": str(a.pk), "url": a.get_absolute_url(), "name": a.name}
                        for a in grant.site.assets.defer("contents")
                    ],
                    "permissions": ["read", "draft"],
                }
            )
        try:
            data = payload(request)
            if set(data) - {"page_id", "title", "html", "version", "slug"}:
                return error("Only page drafts are accepted", 400)
            if not isinstance(data.get("title"), str) or not isinstance(
                data.get("html"), str
            ):
                return error("Title and HTML are required", 400)
            p = services.save_page(
                grant.site,
                grant.user,
                data.get("page_id"),
                data["title"],
                data["html"],
                data.get("version"),
                source="builder",
                new_slug=data.get("slug"),
            )
        except services.Conflict as e:
            return error(e.messages[0], 409)
        except Page.DoesNotExist:
            return error("Page not found", 404)
        except (ValidationError, ValueError, TypeError, IntegrityError) as e:
            return error(
                "Draft rejected: "
                + (
                    e.messages[0] if isinstance(e, ValidationError) else "invalid input"
                ),
                400,
            )
        return JsonResponse(
            {
                "id": str(p.pk),
                "version": p.version,
                "status": "draft",
                "review_url": f"/studio/{grant.site.slug}/pages/{p.pk}/",
            },
            status=201,
        )


def reply(text):
    return JsonResponse(
        {
            "type": 4,
            "data": {"content": text, "flags": 64, "allowed_mentions": {"parse": []}},
        }
    )


@csrf_exempt
@require_POST
def discord_interactions(request):
    if not settings.DISCORD_PUBLIC_KEY:
        return error("Discord is not connected", 503)
    stamp = request.headers.get("X-Signature-Timestamp", "")
    sig = request.headers.get("X-Signature-Ed25519", "")
    try:
        if abs(time.time() - int(stamp)) > 300:
            raise ValueError
        VerifyKey(bytes.fromhex(settings.DISCORD_PUBLIC_KEY)).verify(
            stamp.encode() + request.body, bytes.fromhex(sig)
        )
        data = payload(request)
    except (ValueError, TypeError, BadSignatureError, json.JSONDecodeError):
        return error("Invalid signature", 401)
    if not isinstance(data.get("data", {}), dict) or not isinstance(
        data.get("member", {}), dict
    ):
        return error("Malformed interaction", 400)
    if not isinstance(data.get("member", {}).get("user", {}), dict):
        return error("Malformed member", 400)
    options = data.get("data", {}).get("options", [])
    if not isinstance(options, list) or any(not isinstance(o, dict) for o in options):
        return error("Malformed options", 400)
    for option in options:
        nested = option.get("options", [])
        if not isinstance(nested, list) or any(
            not isinstance(o, dict) or "name" not in o for o in nested
        ):
            return error("Malformed arguments", 400)
    if str(data.get("application_id", "")) != settings.DISCORD_APPLICATION_ID:
        return error("Wrong application", 401)
    if data.get("type") == 1:
        return JsonResponse({"type": 1})
    if data.get("type") != 2 or data.get("data", {}).get("name") != "site":
        return reply("This endpoint handles /site only.")
    binding = (
        DiscordBinding.objects.select_related("site")
        .filter(
            guild_id=data.get("guild_id", ""), channel_id=data.get("channel_id", "")
        )
        .first()
    )
    actor = data.get("member", {}).get("user", {}).get("id")
    account = (
        SocialAccount.objects.select_related("user")
        .filter(provider="discord", uid=actor)
        .first()
    )
    if not binding or not account:
        return reply(
            "This channel and Discord identity are not connected to a website."
        )
    try:
        services.membership(binding.site, account.user)
    except PermissionDenied:
        return reply("You are not an editor for this website.")
    try:
        with transaction.atomic():
            Site.objects.select_for_update().get(pk=binding.site_id)
            services.membership(binding.site, account.user)
            receipt = str(data.get("id", ""))
            if not receipt.isdigit() or len(receipt) > 24:
                return reply("Invalid interaction.")
            if InteractionReceipt.objects.filter(interaction_id=receipt).exists():
                return reply("This request has already been handled.")
            InteractionReceipt.objects.create(interaction_id=receipt)
            opts = data.get("data", {}).get("options", [])
            action = opts[0].get("name") if len(opts) == 1 else None
            args = (
                {o["name"]: o.get("value") for o in opts[0].get("options", [])}
                if opts
                else {}
            )
            if action == "status":
                return reply(
                    f"{binding.site.name}: {binding.site.pages.count()} pages. Open {settings.PUBLIC_ORIGIN}/studio/{binding.site.slug}/ to edit and publish."
                )
            if action != "draft":
                return reply(
                    "Use /site status or /site draft. Publication happens in your website studio."
                )
            if set(args) != {"title", "text"} or not all(
                isinstance(v, str) for v in args.values()
            ):
                return reply("Provide a page title and its text.")
            # Direct slash draft is deliberately plain text, not arbitrary instructions/code.
            p = services.save_page(
                binding.site,
                account.user,
                None,
                args["title"],
                "<p>" + escape(args["text"]).replace("\n", "</p><p>") + "</p>",
                0,
                source="discord",
            )
            return reply(
                f"Draft saved for {binding.site.name}. Review and publish: {settings.PUBLIC_ORIGIN}/studio/{binding.site.slug}/pages/{p.pk}/"
            )
    except (ValidationError, IntegrityError, PermissionDenied):
        return reply(
            "Could not save this draft. Check your title, membership and plan allowance in the studio."
        )
