"""Real SDK stdio -> HTTP -> MySQL acceptance, not a mocked tool response."""

import asyncio
import json
import os
import sys
import tempfile
from datetime import timedelta
from importlib.util import find_spec
from pathlib import Path
from unittest import skipUnless

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import LiveServerTestCase
from django.utils import timezone

from .models import BuilderGrant
from .services import create_site, grant_token


@skipUnless(find_spec("mcp"), "Optional builder SDK not installed")
class MCPAcceptance(LiveServerTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="builder")
        SocialAccount.objects.create(user=self.user, provider="discord", uid="111")
        self.site = create_site(self.user, "First community", "first")
        other = get_user_model().objects.create_user(username="other")
        self.foreign = create_site(other, "Foreign community", "foreign")
        self.grant, token = grant_token(
            self.site,
            self.user,
            "222",
            "333",
            "111",
            timezone.now() + timedelta(minutes=5),
        )
        fd, self.config_path = tempfile.mkstemp(prefix="clan-mcp-test-", suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(
                {
                    "origin": self.live_server_url,
                    "site": self.site.slug,
                    "token": token,
                    "guild": "222",
                    "channel": "333",
                    "actor": "111",
                },
                f,
            )
        self.addCleanup(lambda: Path(self.config_path).unlink(missing_ok=True))

    def test_only_scoped_read_and_draft(self):
        foreign_id = str(self.foreign.pages.get().pk)

        async def run():
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=sys.executable,
                args=[
                    str(settings.BASE_DIR / "scripts/builder_mcp.py"),
                    "--config",
                    self.config_path,
                ],
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    self.assertEqual(
                        {t.name for t in listing.tools}, {"read_site", "draft_page"}
                    )

                    def content(r):
                        return " ".join(v.text for v in r.content if hasattr(v, "text"))

                    result = await session.call_tool("read_site", {})
                    self.assertIn("First community", content(result))
                    self.assertNotIn("Foreign community", content(result))
                    result = await session.call_tool(
                        "draft_page",
                        {
                            "draft": {
                                "title": "Created via MCP",
                                "html": "<p>Hello team</p>",
                            }
                        },
                    )
                    self.assertIn('"status": "draft"', content(result))
                    result = await session.call_tool(
                        "draft_page",
                        {
                            "draft": {
                                "title": "Wrong tenant",
                                "html": "<p>no</p>",
                                "page_id": foreign_id,
                                "version": 1,
                            }
                        },
                    )
                    self.assertIn("Draft rejected", content(result))
                    for forbidden in ["site", "origin", "config", "publish"]:
                        result = await session.call_tool(
                            "draft_page",
                            {
                                "draft": {
                                    "title": "Blocked",
                                    "html": "x",
                                    forbidden: "anything",
                                }
                            },
                        )
                        self.assertTrue(result.is_error)

        asyncio.run(run())
        self.assertEqual(self.site.pages.count(), 2)
        self.assertEqual(self.foreign.pages.count(), 1)
        self.assertFalse(self.site.pages.filter(published_at__isnull=False).exists())

    def test_revoked_bridge_cannot_read(self):
        BuilderGrant.objects.filter(pk=self.grant.pk).update(revoked_at=timezone.now())

        async def run():
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=sys.executable,
                args=[
                    str(settings.BASE_DIR / "scripts/builder_mcp.py"),
                    "--config",
                    self.config_path,
                ],
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    r = await session.call_tool("read_site", {})
                    text = " ".join(v.text for v in r.content if hasattr(v, "text"))
                    self.assertIn("Read failed", text)
                    self.assertNotIn("First community", text)

        asyncio.run(run())
