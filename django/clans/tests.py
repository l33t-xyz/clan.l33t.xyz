import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO

from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from nacl.signing import SigningKey
from PIL import Image

from . import services
from .models import (
    Asset,
    DiscordBinding,
    Membership,
    Page,
)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class Fixture(TestCase):
    def setUp(self):
        U = get_user_model()
        self.a = U.objects.create_user(username="alpha")
        self.b = U.objects.create_user(username="bravo")
        self.sa = services.create_site(self.a, "Alpha", "alpha")
        self.sb = services.create_site(self.b, "Bravo", "bravo")
        self.pa = self.sa.pages.get()
        self.pb = self.sb.pages.get()
        self.client.force_login(self.a)

    def image(self, name="test.png"):
        b = BytesIO()
        Image.new("RGB", (10, 10), "green").save(b, "PNG")
        return SimpleUploadedFile(name, b.getvalue(), content_type="image/png")

    def asset(self, site=None, user=None):
        return services.upload(site or self.sa, user or self.a, self.image())

    def save(self, html="<p>Hello</p>", **kw):
        return services.save_page(
            self.sa,
            self.a,
            self.pa.pk,
            kw.get("title", "Hello"),
            html,
            kw.get("version", self.pa.version),
        )


class ClanTests(Fixture):
    def test_mysql_engine_and_blob(self):
        from django.db import connection

        self.assertEqual(connection.vendor, "mysql")
        with connection.cursor() as c:
            c.execute("SHOW COLUMNS FROM clans_asset LIKE 'contents'")
            self.assertEqual(c.fetchone()[1], "longblob")

    def test_draft_not_public(self):
        self.assertEqual(Client().get("/s/alpha/").status_code, 404)

    def test_published_snapshot_is_independent(self):
        services.publish(self.sa, self.a, self.pa.pk, 1)
        self.pa.refresh_from_db()
        self.save("<p>Secret new draft</p>", title="New private title")
        response = Client().get("/s/alpha/")
        self.assertNotContains(response, "Secret new draft")
        self.assertNotContains(response, "New private title")

    def test_stale_draft_rejected(self):
        self.save()
        with self.assertRaises(services.Conflict):
            self.save("<p>stale</p>")

    def test_stale_publish_rejected(self):
        self.save()
        with self.assertRaises(services.Conflict):
            services.publish(self.sa, self.a, self.pa.pk, 1)

    def test_cross_tenant_service(self):
        with self.assertRaises(PermissionDenied):
            services.save_page(self.sb, self.a, self.pb.pk, "oops", "x", 1)

    def test_cross_tenant_page_id(self):
        with self.assertRaises(Page.DoesNotExist):
            services.save_page(self.sa, self.a, self.pb.pk, "oops", "x", 1)

    def test_studio_does_not_list_foreign_site(self):
        r = self.client.get("/studio/")
        self.assertContains(r, "Alpha")
        self.assertNotContains(r, "Bravo")

    def test_cross_tenant_all_routes(self):
        for suffix in [
            "",
            "images/",
            "settings/",
            "team/",
            "builder/",
            "pages/new/",
            f"pages/{self.pb.pk}/",
            "preview/home/",
        ]:
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    self.client.get("/studio/bravo/" + suffix).status_code, 404
                )

    def test_cross_tenant_write_routes(self):
        for suffix in [
            f"pages/{self.pb.pk}/",
            f"pages/{self.pb.pk}/publish/",
            "upload/",
            "settings/",
            "team/",
        ]:
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    self.client.post("/studio/bravo/" + suffix, {}).status_code, 404
                )

    def test_foreign_revision_hidden(self):
        r = self.pb.revisions.get()
        self.assertEqual(
            self.client.post(
                f"/studio/alpha/pages/{self.pa.pk}/restore/{r.pk}/", {"version": 1}
            ).status_code,
            404,
        )

    def test_draft_asset_private(self):
        a = self.asset()
        self.assertEqual(Client().get(a.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(a.get_absolute_url()).status_code, 200)

    def test_foreign_asset_hidden(self):
        a = self.asset(self.sb, self.b)
        self.assertEqual(self.client.get(a.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(f"/s/alpha/media/{a.pk}/").status_code, 404)

    def test_published_asset_public_and_unpublished_revoked(self):
        a = self.asset()
        p = self.save('<p>Hi</p><img src="' + a.get_absolute_url() + '" alt="test">')
        services.publish(self.sa, self.a, p.pk, p.version)
        self.assertEqual(Client().get(a.get_absolute_url()).status_code, 200)
        p.refresh_from_db()
        services.publish(self.sa, self.a, p.pk, p.version, True)
        self.assertEqual(Client().get(a.get_absolute_url()).status_code, 404)

    def test_xss_stripped(self):
        p = self.save(
            '<script>alert(1)</script><p onclick="alert(1)">Ok</p><a href="javascript:alert(1)">bad</a><iframe src="https://evil.test"></iframe>'
        )
        self.assertNotIn("<script", p.draft_html)
        self.assertNotIn("onclick", p.draft_html)
        self.assertNotIn("javascript:", p.draft_html)
        self.assertNotIn("<iframe", p.draft_html)

    def test_foreign_and_external_images_rejected(self):
        a = self.asset(self.sb, self.b)
        for url in [
            a.get_absolute_url(),
            "https://example.com/a.png",
            "data:image/svg+xml,xxx",
            "//example.com/a",
        ]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                self.save('<img src="' + url + '">')

    def test_image_decode_and_mime(self):
        a = self.asset()
        self.assertEqual(a.content_type, "image/webp")
        self.assertTrue(bytes(a.contents).startswith(b"RIFF"))

    def test_invalid_image_rejected(self):
        for raw in [
            b'<svg onload="alert(1)"></svg>',
            b"not an image",
            b"x" * (2 * 1024 * 1024 + 1),
        ]:
            with self.assertRaises(ValidationError):
                services.upload(self.sa, self.a, SimpleUploadedFile("x.png", raw))

    def test_storage_quota(self):
        self.sa.storage_limit = 1
        self.sa.save()
        with self.assertRaises(ValidationError):
            self.asset()
        with self.assertRaises(ValidationError):
            self.save()

    def test_page_quota(self):
        self.sa.page_limit = 1
        self.sa.save()
        with self.assertRaises(ValidationError):
            services.save_page(self.sa, self.a, None, "new", "<p>hello</p>", 0)

    def test_duplicate_and_reserved_slug(self):
        for s in ["admin", "Aaa", "foo--bar", "-foo", "bad/slash"]:
            with self.subTest(slug=s), self.assertRaises(ValidationError):
                services.create_site(self.a, "Test", s)

    def test_empty_title_invalid(self):
        with self.assertRaises(ValidationError):
            self.save(title="   ")

    def test_long_page_invalid(self):
        with self.assertRaises(ValidationError):
            self.save("x" * 100001)

    def test_revision_restore_draft_only(self):
        old = self.pa.revisions.get()
        self.save("<p>New</p>")
        self.pa.refresh_from_db()
        r = self.client.post(
            f"/studio/alpha/pages/{self.pa.pk}/restore/{old.pk}/",
            {"version": self.pa.version},
        )
        self.assertEqual(r.status_code, 302)
        self.pa.refresh_from_db()
        self.assertEqual(self.pa.draft_html, old.html)
        self.assertIsNone(self.pa.published_at)

    def test_editor_cannot_settings_team_grants(self):
        Membership.objects.create(site=self.sb, user=self.a, role="editor")
        for path in ["settings/", "team/"]:
            self.assertEqual(
                self.client.post("/studio/bravo/" + path, {}).status_code, 404
            )

    def test_editor_can_draft(self):
        Membership.objects.create(site=self.sb, user=self.a, role="editor")
        p = services.save_page(self.sb, self.a, self.pb.pk, "Updated", "<p>ok</p>", 1)
        self.assertEqual(p.title, "Updated")

    def test_membership_removed_immediately(self):
        Membership.objects.filter(site=self.sa, user=self.a).delete()
        self.assertEqual(self.client.get("/studio/alpha/").status_code, 404)

    def test_settings_links_reject_javascript_foreign_and_credentials(self):
        for url in [
            "javascript:alert(1)",
            "https://paypal.me.evil.test/x",
            "https://user:pass@paypal.me/x",
            "http://paypal.me/x",
        ]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                services.configure(
                    self.sa, self.a, {"name": "Alpha", "donation_url": url}
                )

    def test_foreign_hero_rejected(self):
        a = self.asset(self.sb, self.b)
        with self.assertRaises(Asset.DoesNotExist):
            services.configure(self.sa, self.a, {"name": "Alpha", "hero": str(a.pk)})

    def test_csrf_enforced(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.a)
        self.assertEqual(
            c.post(
                f"/studio/alpha/pages/{self.pa.pk}/",
                {"title": "x", "html": "x", "version": 1},
            ).status_code,
            403,
        )

    def test_security_headers(self):
        r = self.client.get("/studio/alpha/")
        self.assertEqual(r["Cache-Control"], "private, no-store")
        self.assertIn("object-src 'none'", r["Content-Security-Policy"])

    def test_demo_disabled_hosted(self):
        with override_settings(MODE="production"):
            self.assertEqual(Client().post("/demo/").status_code, 404)

    def test_demo_session_isolated(self):
        c = Client()
        r = c.post("/demo/")
        self.assertEqual(r.status_code, 302)
        self.assertNotEqual(c.session["_auth_user_id"], str(self.a.pk))

    def test_no_password_signup(self):
        self.assertNotEqual(Client().get("/accounts/signup/").status_code, 200)

    def test_oauth_immutable_subject(self):
        from django.test import RequestFactory

        from .auth import DiscordAdapter

        social = SocialLogin(
            user=get_user_model()(),
            account=SocialAccount(
                provider="discord", uid="123456", extra_data={"global_name": "Friendly"}
            ),
        )
        u = DiscordAdapter().populate_user(
            RequestFactory().get("/"), social, {"username": "Mutable"}
        )
        self.assertEqual(u.username, "discord_123456")

    def test_oauth_no_email_linking(self):
        from django.conf import settings

        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION)

    def test_foreign_tenant_subdomain(self):
        services.publish(self.sa, self.a, self.pa.pk, 1)
        with override_settings(
            CLAN_BASE_DOMAIN="clan.example.test", ALLOWED_HOSTS=[".clan.example.test"]
        ):
            self.assertEqual(
                Client()
                .get("/s/alpha/", HTTP_HOST="bravo.clan.example.test")
                .status_code,
                404,
            )


class BuilderTests(Fixture):
    def setUp(self):
        super().setUp()
        SocialAccount.objects.create(user=self.a, provider="discord", uid="111")
        self.grant, self.token = services.grant_token(
            self.sa, self.a, "222", "333", "111", timezone.now() + timedelta(hours=1)
        )
        self.headers = {
            "HTTP_AUTHORIZATION": "Bearer " + self.token,
            "HTTP_X_DISCORD_GUILD": "222",
            "HTTP_X_DISCORD_CHANNEL": "333",
            "HTTP_X_DISCORD_USER": "111",
        }

    def post(self, data):
        return self.client.post(
            "/api/builder/",
            json.dumps(data),
            content_type="application/json",
            **self.headers,
        )

    def test_api_reads_one_tenant(self):
        r = self.client.get("/api/builder/", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Bravo", r.content.decode())

    def test_context_mismatch(self):
        for key in self.headers:
            h = dict(self.headers)
            h[key] = "wrong"
            self.assertEqual(self.client.get("/api/builder/", **h).status_code, 403)

    def test_cannot_choose_tenant_or_publish(self):
        for extra in [{"site": "bravo"}, {"publish": True}, {"action": "delete"}]:
            self.assertEqual(
                self.post({"title": "hi", "html": "<p>x</p>", **extra}).status_code, 400
            )

    def test_cross_tenant_page(self):
        self.assertEqual(
            self.post(
                {"page_id": str(self.pb.pk), "title": "bad", "html": "x", "version": 1}
            ).status_code,
            404,
        )

    def test_revoke(self):
        self.grant.revoked_at = timezone.now()
        self.grant.save()
        self.assertEqual(
            self.client.get("/api/builder/", **self.headers).status_code, 403
        )

    def test_expired(self):
        self.grant.expires_at = timezone.now() - timedelta(seconds=1)
        self.grant.save()
        self.assertEqual(
            self.client.get("/api/builder/", **self.headers).status_code, 403
        )

    def test_removed_member(self):
        Membership.objects.filter(site=self.sa, user=self.a).delete()
        self.assertEqual(
            self.client.get("/api/builder/", **self.headers).status_code, 403
        )

    def test_api_drafts_never_publish(self):
        r = self.post({"title": "Bot draft", "html": "<h2>Hello</h2>"})
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(Page.objects.get(pk=r.json()["id"]).published_at)

    def test_api_stale_conflict(self):
        self.save()
        self.assertEqual(
            self.post(
                {"page_id": str(self.pa.pk), "title": "Bot", "html": "x", "version": 1}
            ).status_code,
            409,
        )

    def test_malformed(self):
        for data in [[], {"title": [], "html": "x"}, {"title": "X", "html": []}]:
            self.assertEqual(self.post(data).status_code, 400)

    def test_token_only_hashed(self):
        self.assertNotEqual(self.grant.token_hash, self.token)
        self.assertEqual(len(self.grant.token_hash), 64)


class DiscordTests(Fixture):
    def setUp(self):
        super().setUp()
        self.key = SigningKey.generate()
        SocialAccount.objects.create(user=self.a, provider="discord", uid="111")
        DiscordBinding.objects.create(site=self.sa, guild_id="222", channel_id="333")
        self.override = override_settings(
            DISCORD_PUBLIC_KEY=self.key.verify_key.encode().hex(),
            DISCORD_APPLICATION_ID="444",
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

    def call(self, data, stamp=None):
        body = json.dumps(data)
        stamp = str(stamp or int(time.time()))
        signature = self.key.sign(stamp.encode() + body.encode()).signature.hex()
        return Client().post(
            "/discord/interactions/",
            body,
            content_type="application/json",
            HTTP_X_SIGNATURE_TIMESTAMP=stamp,
            HTTP_X_SIGNATURE_ED25519=signature,
        )

    def data(self, action="status"):
        return {
            "id": "777",
            "application_id": "444",
            "type": 2,
            "guild_id": "222",
            "channel_id": "333",
            "member": {"user": {"id": "111"}},
            "data": {
                "name": "site",
                "options": [
                    {
                        "name": action,
                        "options": [
                            {"name": "title", "value": "Discord draft"},
                            {"name": "text", "value": "<script>hello</script>"},
                        ],
                    }
                ],
            },
        }

    def test_ping(self):
        self.assertEqual(
            self.call({"type": 1, "application_id": "444"}).json(), {"type": 1}
        )

    def test_wrong_application(self):
        self.assertEqual(
            self.call({"type": 1, "application_id": "wrong"}).status_code, 401
        )

    def test_unsigned(self):
        self.assertEqual(
            Client()
            .post("/discord/interactions/", "{}", content_type="application/json")
            .status_code,
            401,
        )

    def test_old_signature(self):
        self.assertEqual(
            self.call(self.data(), int(time.time()) - 600).status_code, 401
        )

    def test_discord_draft_and_replay(self):
        r = self.call(self.data("draft"))
        self.assertIn("Draft saved", r.json()["data"]["content"])
        self.assertEqual(self.sa.pages.count(), 2)
        self.call(self.data("draft"))
        self.assertEqual(self.sa.pages.count(), 2)
        p = self.sa.pages.get(slug="discord-draft")
        self.assertNotIn("<script>", p.draft_html)
        self.assertIsNone(p.published_at)

    def test_wrong_channel(self):
        d = self.data("draft")
        d["channel_id"] = "999"
        self.call(d)
        self.assertEqual(self.sa.pages.count(), 1)

    def test_foreign_actor(self):
        SocialAccount.objects.create(user=self.b, provider="discord", uid="999")
        d = self.data("draft")
        d["member"]["user"]["id"] = "999"
        self.call(d)
        self.assertEqual(self.sa.pages.count(), 1)


class ReviewTests(Fixture):
    def test_legacy_address_reserved(self):
        with self.assertRaises(ValidationError):
            services.create_site(self.a, "Existing clan", "amazon")

    def test_import_dry_run_and_safe_source(self):
        from .importing import import_pages

        data = {
            "records": [
                {
                    "fields": {
                        "title": "Story",
                        "slug": "story",
                        "content": "# Welcome\n<script>alert(1)</script>",
                        "attachments": [{"url": "http://127.0.0.1/private"}],
                    }
                }
            ]
        }
        report = import_pages(self.sa, self.a, data)
        self.assertFalse(report["applied"])
        self.assertEqual(self.sa.pages.count(), 1)
        report = import_pages(self.sa, self.a, data, True)
        p = self.sa.pages.get(slug="story")
        self.assertIsNone(p.published_at)
        self.assertNotIn("<script>", p.draft_html)
        self.assertEqual(report["attachments_deferred"], 1)

    def test_import_never_overwrites(self):
        from .importing import import_pages

        with self.assertRaises(ValidationError):
            import_pages(
                self.sa,
                self.a,
                {"pages": [{"title": "Overwrite", "slug": "home", "content": "oops"}]},
                True,
            )
        self.pa.refresh_from_db()
        self.assertEqual(self.pa.title, "Welcome")

    def test_import_all_or_nothing_quota(self):
        from .importing import import_pages

        self.sa.page_limit = 2
        self.sa.save()
        with self.assertRaises(ValidationError):
            import_pages(
                self.sa,
                self.a,
                {
                    "pages": [
                        {"title": "a", "slug": "a", "content": "x"},
                        {"title": "b", "slug": "b", "content": "y"},
                    ]
                },
                True,
            )
        self.assertEqual(self.sa.pages.count(), 1)

    def test_cross_tenant_import(self):
        from .importing import import_pages

        with self.assertRaises(PermissionDenied):
            import_pages(
                self.sb,
                self.a,
                {"pages": [{"title": "a", "slug": "a", "content": "x"}]},
                True,
            )

    def test_tenant_subdomain_root_and_host_boundary(self):
        services.publish(self.sa, self.a, self.pa.pk, 1)
        a = self.asset(self.sb, self.b)
        with override_settings(
            CLAN_BASE_DOMAIN="clan.example.test", ALLOWED_HOSTS=[".clan.example.test"]
        ):
            c = Client()
            self.assertEqual(
                c.get("/", HTTP_HOST="alpha.clan.example.test").status_code, 200
            )
            for path in [
                "/studio/",
                "/api/builder/",
                "/s/bravo/",
                a.get_absolute_url(),
            ]:
                self.assertEqual(
                    c.get(path, HTTP_HOST="alpha.clan.example.test").status_code, 404
                )

    def test_oversized_request_rejected_early(self):
        self.assertEqual(
            self.client.post(
                "/studio/alpha/upload/",
                b"x" * 10,
                content_type="application/octet-stream",
                CONTENT_LENGTH=str(4 * 1024 * 1024),
            ).status_code,
            413,
        )

    def test_all_studio_templates(self):
        for suffix in [
            "",
            "images/",
            "settings/",
            "team/",
            "builder/",
            "pages/new/",
            f"pages/{self.pa.pk}/",
        ]:
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    self.client.get("/studio/alpha/" + suffix).status_code, 200
                )


@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "discord": {
            "SCOPE": ["identify"],
            "APP": {
                "client_id": "synthetic-client",
                "secret": "synthetic-test-secret",
                "key": "",
            },
        }
    }
)
class OAuthFlowTests(Fixture):
    def test_oauth_state_and_callback(self):
        from unittest.mock import patch
        from urllib.parse import parse_qs, urlparse

        import requests

        c = Client()
        start = c.post("/accounts/discord/login/")
        self.assertEqual(start.status_code, 302)
        query = parse_qs(urlparse(start.url).query)
        self.assertEqual(query["scope"], ["identify"])
        self.assertIn("state", query)

        def response(method, url, **kwargs):
            r = requests.Response()
            r.status_code = 200
            r.headers["content-type"] = "application/json"
            data = (
                {
                    "access_token": "synthetic-test-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                }
                if "oauth2/token" in url
                else {
                    "id": "987654",
                    "username": "nickname",
                    "global_name": "Captain",
                    "discriminator": "0",
                    "avatar": None,
                }
            )
            r._content = json.dumps(data).encode()
            return r

        with patch("requests.sessions.Session.request", side_effect=response):
            end = c.get(
                "/accounts/discord/login/callback/",
                {"code": "synthetic-code", "state": query["state"][0]},
            )
        self.assertEqual(end.status_code, 302)
        self.assertIn("_auth_user_id", c.session)
        user = get_user_model().objects.get(pk=c.session["_auth_user_id"])
        self.assertEqual(user.username, "discord_987654")
        from allauth.socialaccount.models import SocialToken

        self.assertEqual(SocialToken.objects.count(), 0)
        # Single-use state cannot authenticate another session.
        with patch("requests.sessions.Session.request") as network:
            Client().get(
                "/accounts/discord/login/callback/",
                {"code": "synthetic-code", "state": query["state"][0]},
            )
            network.assert_not_called()

    def test_missing_state_rejected_without_network(self):
        from unittest.mock import patch

        with patch("requests.sessions.Session.request") as network:
            c = Client()
            c.get("/accounts/discord/login/callback/", {"code": "synthetic-code"})
            self.assertNotIn("_auth_user_id", c.session)
            network.assert_not_called()


class QuotaRaceTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="race")
        self.site = services.create_site(self.user, "Race", "race")
        self.site.page_limit = 2
        self.site.save()

    def worker(self, name):
        close_old_connections()
        try:
            services.save_page(self.site, self.user, None, name, "<p>new</p>", 0)
            return "saved"
        except ValidationError:
            return "blocked"
        finally:
            close_old_connections()

    def test_concurrent_last_page_slot(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.worker, ["one", "two"]))
        self.assertCountEqual(results, ["saved", "blocked"])
        self.assertEqual(self.site.pages.count(), 2)

    def test_concurrent_same_version(self):
        page = self.site.pages.get()

        def edit(text):
            close_old_connections()
            try:
                services.save_page(
                    self.site, self.user, page.pk, "Updated", "<p>" + text + "</p>", 1
                )
                return "saved"
            except services.Conflict:
                return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, ["one", "two"]))
        self.assertCountEqual(results, ["saved", "conflict"])


class MalformedOwnerActions(Fixture):
    def test_bad_membership_id_is_client_error(self):
        self.assertEqual(
            self.client.post(
                "/studio/alpha/team/", {"remove": "not-a-number"}
            ).status_code,
            400,
        )

    def test_bad_builder_grant_id_is_client_error(self):
        self.assertEqual(
            self.client.post(
                "/studio/alpha/builder/", {"revoke": "not-a-uuid"}
            ).status_code,
            400,
        )

    def test_non_web_image_rejected(self):
        b = BytesIO()
        Image.new("RGB", (5, 5), "green").save(b, "BMP")
        with self.assertRaises(ValidationError):
            services.upload(
                self.sa, self.a, SimpleUploadedFile("image.bmp", b.getvalue())
            )
