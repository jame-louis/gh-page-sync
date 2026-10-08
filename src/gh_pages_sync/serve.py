"""Serve a synced directory locally (stdlib ``http.server``).

Dotfiles (e.g. ``.git/``) are hidden from the served tree, and directory
traversal outside the served root is rejected.
"""

from __future__ import annotations

import http.server
import socketserver
from pathlib import Path


def build_handler(directory: Path):
    directory = directory.resolve()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def translate_path(self, path: str) -> str:
            # SimpleHTTPRequestHandler already rejects escapes; keep it inside root.
            translated = super().translate_path(path)
            rel = Path(translated).resolve()
            if rel != directory and directory not in rel.parents:
                return ""
            rel_part = rel.relative_to(directory)
            if any(p.startswith(".") for p in rel_part.parts):
                return ""
            return translated

        def log_message(self, fmt, *args):
            print(f"[gh-pages-sync] {self.address_string()} {fmt % args}")

    return Handler


def serve(directory: Path, *, host: str = "127.0.0.1", port: int = 8000) -> None:
    directory = directory.resolve()
    if not directory.is_dir():
        raise SystemExit(f"Not a directory: {directory}")
    handler = build_handler(directory)
    with socketserver.ThreadingTCPServer((host, port), handler) as httpd:
        print(f"Serving {directory} at http://{host}:{port}/ (Ctrl-C to stop)")
        httpd.serve_forever()