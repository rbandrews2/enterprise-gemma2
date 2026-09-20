"""Serve the recovered Core build on loopback with outbound browser access blocked.

This inspection server is not a deployment server or an authenticated backend.
"""
from functools import partial
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

BUILD = Path(__file__).resolve().parents[1] / ".local-recovery/core-build-baseline/dist"


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "; ".join([
            "default-src 'none'", "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob:",
            "font-src 'self' data:", "media-src 'self' blob:",
            "connect-src 'none'", "worker-src 'none'", "manifest-src 'self'",
            "form-action 'none'", "frame-ancestors 'none'", "base-uri 'none'",
        ]))
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):
        if self.headers.get("Host") not in {"127.0.0.1:8082", "localhost:8082"}:
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if not Path(self.translate_path(path)).is_file() and not Path(path).suffix:
            self.path = "/index.html"
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="core-build-baseline")
    args = parser.parse_args()
    if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.name):
        parser.error("name must contain lowercase letters, digits, hyphen or underscore")
    BUILD = BUILD.parents[1] / args.name / "dist"
    if not (BUILD / "index.html").is_file():
        raise SystemExit("Build the isolated baseline first.")
    print("Core inspection only: http://127.0.0.1:8082; external requests blocked", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8082), partial(Handler, directory=str(BUILD))).serve_forever()
