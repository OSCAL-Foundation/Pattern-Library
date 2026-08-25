#!/usr/bin/env python3
"""
serve.py: serve the Pattern Library site the way GitHub Pages will.

The published site is docs/ with one thing added: the pattern artifacts, which
live at summit/ because they are the repository's product rather than part of
its website. .github/workflows/pages.yml copies them:

    docs/      ->  _site/
    summit/    ->  _site/patterns/summit/

Doing that copy locally means re-running it after every edit. This serves the
same shape without one: docs/ is the root, and any request under
/patterns/summit/ is answered from summit/ where it actually sits. Edit a file
and refresh; nothing is written and nothing is generated.

    python3 tools/serve.py
    python3 tools/serve.py --port 8080
    python3 tools/serve.py --page analysis/index.html
    python3 tools/serve.py --no-open

To check the real deploy artifact rather than this overlay, do what the
workflow does:

    rm -rf _site && mkdir -p _site/patterns
    cp -r docs/. _site/ && cp -r summit _site/patterns/summit
    python3 -m http.server -d _site 8000

Nothing is installed. Press Ctrl-C to stop.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import os
import socket
import socketserver
import sys
import threading
import webbrowser

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
SITE_ROOT = os.path.join(REPO_ROOT, "docs")
ARTIFACT_ROOT = os.path.join(REPO_ROOT, "summit")

# Where the workflow puts summit/, and so where a page's links point.
ARTIFACT_PREFIX = "/patterns/summit"

# Not 8000. Each analysis ships its own server defaulting to that, and on WSL a
# Windows-side one answers 127.0.0.1 here without showing up in `ss`, so the
# collision is silent and serves the wrong site.
DEFAULT_PORT = 8100


class Handler(http.server.SimpleHTTPRequestHandler):
    """docs/ as the root, with summit/ overlaid where the deploy puts it."""

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".js": "text/javascript",
        ".css": "text/css",
        ".puml": "text/plain",
        ".map": "application/json",
    }

    def translate_path(self, path):
        head = path.split("?", 1)[0].split("#", 1)[0]
        if head == ARTIFACT_PREFIX or head.startswith(ARTIFACT_PREFIX + "/"):
            # Rebase onto summit/ and let the base class resolve it: its own
            # translate_path is what drops .. and absolute components, and it
            # clamps to whatever self.directory is. Pointing that at the
            # repository root instead would let ../ out of summit/ and reach
            # .git, which is why the swap is to the artifact root itself.
            saved, self.directory = self.directory, ARTIFACT_ROOT
            try:
                return super().translate_path(path[len(ARTIFACT_PREFIX):] or "/")
            finally:
                self.directory = saved
        return super().translate_path(path)

    def end_headers(self):
        #  Regenerating an analysis between refreshes should show the new data.
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else ""
        #  Only failures are worth printing. A path that does not resolve is
        #  the thing this server exists to make visible.
        if str(status).startswith(("4", "5")):
            sys.stderr.write(f"  {status}  {args[0]}\n")


def free_port(preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with contextlib.closing(socket.socket()) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"no free port between {preferred} and {preferred + 19}")


def claim_port(preferred: int) -> int:
    """Fail rather than move. A caller that opens a fixed URL -- the debugger
    launch config does -- would otherwise attach to whatever stale server is
    still holding the port and show content nobody is editing."""
    with contextlib.closing(socket.socket()) as s:
        try:
            s.bind(("127.0.0.1", preferred))
        except OSError:
            raise SystemExit(
                f"port {preferred} is already in use.\n"
                f"\n"
                f"  Something is serving there and it is not this. Opening the "
                f"URL anyway would\n"
                f"  show you that server's content, which is the failure this "
                f"flag exists to prevent.\n"
                f"\n"
                f"  On WSL, check Windows too: a listener on the Windows side "
                f"answers 127.0.0.1\n"
                f"  here and does not appear in `ss -ltnp`. An analysis's own "
                f"serve.cmd is the\n"
                f"  usual culprit.\n"
                f"      WSL      ss -ltnp | grep {preferred}\n"
                f"      Windows  netstat -ano | findstr :{preferred}\n"
                f"\n"
                f"  Or run without --exact-port to take the next free port.")
    return preferred


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--exact-port", action="store_true",
                   help="fail if --port is taken instead of moving to the next")
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.add_argument("--page", default="index.html", help="the page to open")
    a = p.parse_args()

    for d in (SITE_ROOT, ARTIFACT_ROOT):
        if not os.path.isdir(d):
            raise SystemExit(f"not found: {d}. Run this from a checkout of the "
                             f"Pattern-Library repository.")

    port = claim_port(a.port) if a.exact_port else free_port(a.port)
    url = f"http://127.0.0.1:{port}/{a.page.lstrip('/')}"
    handler = functools.partial(Handler, directory=SITE_ROOT)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        analyses = sorted(
            e for e in os.listdir(os.path.join(SITE_ROOT, "analysis"))
            if os.path.isdir(os.path.join(SITE_ROOT, "analysis", e))
        )
        print(f"Serving {SITE_ROOT}")
        print(f"  with summit/ overlaid at {ARTIFACT_PREFIX}/")
        print(f"  {url}")
        print(f"  {len(analyses)} analysis area(s): " + "  ".join(analyses))
        print("Only 4xx and 5xx responses are logged. Ctrl-C to stop.\n")
        if not a.no_open:
            threading.Timer(0.4, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
