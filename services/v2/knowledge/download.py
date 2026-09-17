"""Bounded operator-only downloads; never accepts a URL from an API request."""
import time
from urllib.parse import urljoin

import httpx
from .models import Source, approved_url

MAX_BYTES = 100 * 1024 * 1024


class DownloadError(Exception):
    pass


def download(source: Source, client: httpx.Client, max_bytes: int = MAX_BYTES):
    url = source.url
    allowed = {source.url, *source.allowed_redirects}
    started = time.monotonic()
    for _ in range(4):
        approved_url(url)
        if url not in allowed:
            raise DownloadError("redirect_not_approved")
        with client.stream("GET", url, follow_redirects=False, timeout=30) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                url = urljoin(url, response.headers.get("location", ""))
                continue
            if response.status_code != 200:
                raise DownloadError(f"http_{response.status_code}")
            mime = response.headers.get("content-type", "").split(";")[0].lower().strip()
            expected = {"application/pdf"} if source.kind == "pdf" else {"text/html", "application/xhtml+xml"}
            if mime not in expected:
                raise DownloadError("unexpected_content_type")
            length = response.headers.get("content-length")
            if length and (not length.isdigit() or int(length) > max_bytes):
                raise DownloadError("invalid_or_oversized_content_length")
            data = bytearray()
            for chunk in response.iter_bytes(65536):
                if time.monotonic() - started > 120:
                    raise DownloadError("download_deadline_exceeded")
                if len(data) + len(chunk) > max_bytes:
                    raise DownloadError("document_too_large")
                data.extend(chunk)
            if not data:
                raise DownloadError("empty_document")
            if source.kind == "pdf" and not data.startswith(b"%PDF-"):
                raise DownloadError("invalid_pdf_signature")
            if source.kind == "html" and b"<html" not in bytes(data[:8192]).lower():
                raise DownloadError("invalid_html_signature")
            return bytes(data), url
    raise DownloadError("too_many_redirects")
