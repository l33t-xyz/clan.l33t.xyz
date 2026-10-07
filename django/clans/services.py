import hashlib
import re
import secrets
import warnings
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urlparse

import nh3
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Asset, AuditEvent, BuilderGrant, Membership, Page, Revision, Site

MAX_HTML = 100_000
MAX_IMAGE = 2 * 1024 * 1024
RESERVED = {
    "www",
    "api",
    "admin",
    "studio",
    "login",
    "accounts",
    "static",
    "media",
    "demo",
    "health",
    "clan",
}


class Conflict(ValidationError):
    pass


def membership(site, user, owner=False):
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied
    q = Membership.objects.filter(site=site, user=user)
    if owner:
        q = q.filter(role="owner")
    if not q.exists():
        raise PermissionDenied


def slug(value, max_length=48):
    if (
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value or "")
        or len(value) > max_length
        or value in RESERVED
    ):
        raise ValidationError("Use lowercase letters, numbers and single hyphens.")
    return value


def clean_link(value, hosts=None):
    if not value:
        return ""
    u = urlparse(value)
    if (
        u.scheme != "https"
        or not u.hostname
        or u.username
        or u.password
        or u.port not in (None, 443)
    ):
        raise ValidationError("Use a secure https:// link.")
    if hosts and u.hostname.lower() not in hosts:
        raise ValidationError("This link is not from a supported provider.")
    return value


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = set()

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.sources.add(dict(attrs).get("src", ""))


def image_sources(html):
    parser = Images()
    parser.feed(html)
    return parser.sources


def sanitize(site, html):
    if not isinstance(html, str) or len(html.encode()) > MAX_HTML:
        raise ValidationError("Page is too large (100 KB maximum).")
    allowed = set(site.assets.values_list("id", flat=True))
    paths = {f"/s/{site.slug}/media/{i}/" for i in allowed}

    def attr(tag, key, value):
        if tag == "img" and key == "src":
            return value if value in paths else None
        if tag == "li" and key == "data-list":
            return value if value in {"ordered", "bullet"} else None
        if key == "class":
            return (
                value
                if value
                in {
                    "ql-align-center",
                    "ql-align-right",
                    "ql-align-justify",
                    "ql-indent-1",
                    "ql-indent-2",
                }
                else None
            )
        return value

    result = nh3.clean(
        html,
        tags={
            "p",
            "br",
            "h2",
            "h3",
            "h4",
            "strong",
            "b",
            "em",
            "i",
            "u",
            "s",
            "ul",
            "ol",
            "li",
            "blockquote",
            "a",
            "img",
            "pre",
            "code",
            "span",
        },
        attributes={
            "a": {"href", "title"},
            "img": {"src", "alt"},
            "li": {"data-list"},
            "*": {"class"},
        },
        attribute_filter=attr,
        url_schemes={"https", "http", "mailto"},
        link_rel="noopener noreferrer nofollow",
    )
    # Reject missing/foreign images instead of silently saving broken cross-tenant references.
    if image_sources(html) - paths:
        raise ValidationError("Use images uploaded to this website's library.")
    return result


def usage(site):
    media = site.assets.aggregate(total=Sum("size_bytes"))["total"] or 0
    pages = sum(
        len(p.draft_html.encode()) + len(p.published_html.encode())
        for p in site.pages.only("draft_html", "published_html")
    )
    history = sum(
        len(r.html.encode()) + len(r.title.encode()) + 256
        for r in Revision.objects.filter(page__site=site).only("html", "title")
    )
    return media + pages + history


def capacity(site, extra):
    if usage(site) + extra > site.storage_limit:
        raise ValidationError(
            "Your website has reached its storage allowance. Contact us to grow your plan."
        )


@transaction.atomic
def create_site(user, name, handle, game="", *, legacy_import=False):
    # Serialize per-user creation to cap free-site abuse.
    type(user).objects.select_for_update().get(pk=user.pk)
    if Membership.objects.filter(user=user, role="owner").count() >= 3:
        raise ValidationError(
            "You can create up to three websites. Contact us for more."
        )
    if handle in settings.LEGACY_RESERVED_SLUGS and not legacy_import:
        raise ValidationError("That address is reserved for an existing community.")
    name = name.strip()
    if not name or len(name) > 100:
        raise ValidationError("Give your website a name (up to 100 characters).")
    site = Site.objects.create(name=name, slug=slug(handle), game=game[:80])
    Membership.objects.create(site=site, user=user, role="owner")
    page = Page.objects.create(
        site=site,
        title="Welcome",
        slug="home",
        draft_html="<h2>Welcome to our corner of the internet.</h2><p>Tell your story. Introduce your crew. Make yourselves at home.</p>",
    )
    Revision.objects.create(
        page=page, title=page.title, html=page.draft_html, version=1, actor=user
    )
    AuditEvent.objects.create(site=site, actor=user, action="site.created")
    return site


@transaction.atomic
def save_page(
    site, user, page_id, title, html, expected, source="editor", new_slug=None
):
    site = Site.objects.select_for_update().get(pk=site.pk)
    membership(site, user)
    title = title.strip()
    if not title or len(title) > 120:
        raise ValidationError("Enter a title of 1–120 characters.")
    cleaned = sanitize(site, html)
    if page_id:
        page = Page.objects.get(site=site, pk=page_id)
        if str(page.version) != str(expected):
            raise Conflict(
                "This page changed elsewhere. Reload before saving so nobody's work is lost."
            )
        capacity(
            site,
            2 * len(cleaned.encode())
            - len(page.draft_html.encode())
            + len(title.encode())
            + 256,
        )
        page.version += 1
    else:
        if site.pages.count() >= site.page_limit:
            raise ValidationError(
                "Your plan's page allowance is full. Contact us to add more pages."
            )
        capacity(site, 2 * len(cleaned.encode()) + len(title.encode()) + 256)
        handle = slug(new_slug or slugify(title), 64)
        if site.pages.filter(slug=handle).exists():
            raise ValidationError("A page already uses that address.")
        page = Page(site=site, slug=handle, position=site.pages.count())
    page.title = title
    page.draft_html = cleaned
    page.save()
    Revision.objects.create(
        page=page,
        title=title,
        html=cleaned,
        version=page.version,
        actor=user,
        source=source,
    )
    AuditEvent.objects.create(
        site=site, actor=user, action="page.drafted", detail=str(page.pk)
    )
    return page


@transaction.atomic
def publish(site, user, page_id, expected, unpublish=False):
    site = Site.objects.select_for_update().get(pk=site.pk)
    membership(site, user)
    page = Page.objects.get(site=site, pk=page_id)
    if str(page.version) != str(expected):
        raise Conflict("Page changed. Reload and review before publishing.")
    if not unpublish:
        capacity(
            site, len(page.draft_html.encode()) - len(page.published_html.encode())
        )
        page.published_html = page.draft_html
        page.published_title = page.title
        page.published_at = timezone.now()
    else:
        page.published_html = ""
        page.published_title = ""
        page.published_at = None
    page.version += 1
    page.save()
    AuditEvent.objects.create(
        site=site,
        actor=user,
        action="page.unpublished" if unpublish else "page.published",
        detail=str(page.pk),
    )
    return page


@transaction.atomic
def upload(site, user, file):
    site = Site.objects.select_for_update().get(pk=site.pk)
    membership(site, user)
    raw = file.read(MAX_IMAGE + 1)
    if len(raw) > MAX_IMAGE:
        raise ValidationError("Choose an image smaller than 2 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(BytesIO(raw))
            if img.format not in {"PNG", "JPEG", "GIF", "WEBP"}:
                raise ValidationError("Choose PNG, JPEG, GIF or WebP.")
            img.verify()
            img = Image.open(BytesIO(raw))
            if img.width * img.height > 20_000_000:
                raise ValidationError("Image dimensions are too large.")
            img = ImageOps.exif_transpose(img)
            img.thumbnail((2400, 2400))
            out = BytesIO()
            img.convert("RGBA" if "A" in img.getbands() else "RGB").save(
                out, format="WEBP", quality=88
            )
            data = out.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValidationError("Upload a valid PNG, JPEG, GIF or WebP image.")
    capacity(site, len(data))
    a = Asset.objects.create(
        site=site,
        name=str(file.name).split("/")[-1][:160],
        content_type="image/webp",
        contents=data,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    AuditEvent.objects.create(
        site=site, actor=user, action="image.uploaded", detail=str(a.pk)
    )
    return a


@transaction.atomic
def configure(site, user, data):
    site = Site.objects.select_for_update().get(pk=site.pk)
    membership(site, user, owner=True)
    name = data.get("name", "").strip()
    if not name or len(name) > 100:
        raise ValidationError("Name must be 1–100 characters.")
    theme = data.get("theme", "forest")
    if theme not in {"forest", "amethyst", "ember", "ocean"}:
        raise ValidationError("Choose a listed theme.")
    site.name = name
    site.tagline = data.get("tagline", "")[:180]
    site.game = data.get("game", "")[:80]
    site.theme = theme
    site.invite_url = clean_link(
        data.get("invite_url", ""), {"discord.gg", "discord.com"}
    )
    site.donation_url = clean_link(
        data.get("donation_url", ""), {"paypal.me", "www.paypal.com", "paypal.com"}
    )
    hero = data.get("hero", "")
    site.hero = Asset.objects.get(site=site, pk=hero) if hero else None
    site.save()
    AuditEvent.objects.create(site=site, actor=user, action="site.settings")
    return site


def grant_token(site, user, guild, channel, discord_id, expires):
    membership(site, user, owner=True)
    if not all(
        re.fullmatch(r"[0-9]{1,24}", str(v)) for v in [guild, channel, discord_id]
    ):
        raise ValidationError("Use numeric Discord IDs.")
    from allauth.socialaccount.models import SocialAccount

    if not SocialAccount.objects.filter(
        user=user, provider="discord", uid=discord_id
    ).exists():
        raise ValidationError("Grant actor must match the owner's Discord identity.")
    token = secrets.token_urlsafe(32)
    grant = BuilderGrant.objects.create(
        site=site,
        user=user,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        guild_id=guild,
        channel_id=channel,
        discord_user_id=discord_id,
        expires_at=expires,
    )
    return grant, token
