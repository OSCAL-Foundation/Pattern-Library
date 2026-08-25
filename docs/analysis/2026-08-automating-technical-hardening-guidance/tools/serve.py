#!/usr/bin/env python3
"""
serve.py: serve the site locally so its pages can load their own content.

Why this exists. Every page here is markup plus data: the markup carries hooks
like data-matrix and data-slot-fill, and assets/site.js fills them from data/ at
load time. Plan section 8 asks for exactly that, so that regenerating data never
touches markup.

The cost of that design is that the site has to be served. A browser gives a
file:// page an opaque origin and blocks fetch() for local files, so opening a
page by double-clicking it leaves every data-driven block showing an error and
every diagram missing. GitHub Pages is unaffected, because it serves over HTTP.
Local review is affected, and local review is what every gate in the build guide
asks for.

    python tools/serve.py
    python tools/serve.py --port 8080
    python tools/serve.py --no-open

Nothing is installed and nothing is written. Press Ctrl-C to stop.
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
SITE_ROOT = os.path.dirname(TOOLS_DIR)


class Handler(http.server.SimpleHTTPRequestHandler):
    """Static files, correct types, and no caching while reviewing."""

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".js": "text/javascript",
        ".css": "text/css",
        ".map": "application/json",
    }

    def end_headers(self):
        #  A reviewer regenerating data between refreshes should see the new
        #  data, not a cached copy of the old.
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else ""
        #  Only failures are worth printing. A missing data file is the thing
        #  this server exists to make visible.
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--no-open", action="store_true",
                   help="do not open a browser")
    p.add_argument("--page", default="index.html",
                   help="the page to open, default index.html")
    a = p.parse_args()

    missing = [d for d in ("data", "assets") if not os.path.isdir(
        os.path.join(SITE_ROOT, d))]
    if missing:
        raise SystemExit(f"{SITE_ROOT} does not look like the site root: "
                         f"missing {', '.join(missing)}")

    port = free_port(a.port)
    url = f"http://127.0.0.1:{port}/{a.page.lstrip('/')}"
    handler = functools.partial(Handler, directory=SITE_ROOT)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {SITE_ROOT}")
        print(f"  {url}")
        pages = sorted(f[:-5] for f in os.listdir(SITE_ROOT)
                       if f.endswith(".html"))
        print(f"  {len(pages)} pages: " + "  ".join(pages))
        print("Only 4xx and 5xx responses are logged. Ctrl-C to stop.\n")
        if not a.no_open:
            threading.Timer(0.4, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
