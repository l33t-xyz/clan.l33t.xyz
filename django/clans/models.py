import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=48, unique=True)
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=180, blank=True)
    theme = models.CharField(
        max_length=20,
        choices=[
            ("forest", "Forest"),
            ("amethyst", "Amethyst"),
            ("ember", "Ember"),
            ("ocean", "Ocean"),
        ],
        default="forest",
    )
    game = models.CharField(max_length=80, blank=True)
    invite_url = models.URLField(blank=True)
    donation_url = models.URLField(blank=True)
    hero = models.ForeignKey(
        "Asset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hero_for",
    )
    plan = models.CharField(
        max_length=10, choices=[("free", "Free"), ("plus", "Plus")], default="free"
    )
    # Provisional operator-configurable allowances, not advertised paid pricing.
    page_limit = models.PositiveIntegerField(default=5)
    storage_limit = models.PositiveBigIntegerField(default=25 * 1024 * 1024)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("site", args=[self.slug])


class Membership(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, choices=[("owner", "Owner"), ("editor", "Editor")]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "user"], name="unique_site_member")
        ]


class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="pages")
    slug = models.SlugField(max_length=64)
    title = models.CharField(max_length=120)
    draft_html = models.TextField(blank=True)
    published_html = models.TextField(blank=True)
    published_title = models.CharField(max_length=120, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    position = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="unique_site_page_slug"
            )
        ]


class Revision(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="revisions")
    title = models.CharField(max_length=120)
    html = models.TextField()
    version = models.PositiveIntegerField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    source = models.CharField(max_length=20, default="editor")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "version"], name="unique_page_revision"
            )
        ]


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=160)
    content_type = models.CharField(max_length=60)
    contents = models.BinaryField()
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("asset", args=[self.site.slug, self.pk])


class BuilderGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, related_name="builder_grants"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    guild_id = models.CharField(max_length=24)
    channel_id = models.CharField(max_length=24)
    discord_user_id = models.CharField(max_length=24)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DiscordBinding(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    guild_id = models.CharField(max_length=24)
    channel_id = models.CharField(max_length=24)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["guild_id", "channel_id"], name="one_site_per_channel"
            )
        ]


class InteractionReceipt(models.Model):
    interaction_id = models.CharField(max_length=24, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditEvent(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=40)
    detail = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
