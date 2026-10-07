#!/usr/bin/env python3
"""Narrow stdio adapter for an isolated tenant agent. No shell/filesystem tools exposed."""

import argparse
import json
import os
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def request(config, method="GET", body=None):
    origin = config["origin"]
    url = urlparse(origin)
    if (
        url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in ("", "/")
    ):
        raise ValueError("Origin must be a bare host URL")
    if url.scheme != "https" and not (
        url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost"}
    ):
        raise ValueError("HTTPS required")
    headers = {
        "Authorization": "Bearer " + config["token"],
        "X-Discord-Guild": config["guild"],
        "X-Discord-Channel": config["channel"],
        "X-Discord-User": config["actor"],
        "Content-Type": "application/json",
    }

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(
        origin.rstrip("/") + "/api/builder/",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    with opener.open(req, timeout=30) as res:
        return json.load(res)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["read", "draft"])
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    path = Path(args.config).expanduser()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd) as f:
        st = os.fstat(f.fileno())
        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_uid != os.getuid()
            or stat.S_IMODE(st.st_mode) & 0o077
        ):
            raise ValueError("Config must be an owner-only regular file")
        config = json.load(f)
    if args.action == "read":
        result = request(config)
    else:
        text = sys.stdin.read(110001)
        if len(text) > 110000:
            raise ValueError("Draft too large")
        body = json.loads(text)
        if not isinstance(body, dict) or set(body) - {
            "page_id",
            "title",
            "html",
            "version",
            "slug",
        }:
            raise ValueError("Only a page draft is accepted")
        result = request(config, "POST", body)
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(
            json.dumps({"error": "Request rejected", "status": e.code}), file=sys.stderr
        )
        sys.exit(1)
    except Exception:
        print(
            json.dumps(
                {
                    "error": "Builder request failed; verify private configuration and network access."
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)
