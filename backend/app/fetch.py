"""Fetch an article's title when the user saves a URL.

The server fetches a URL the user typed, which is a classic SSRF hole: "save"
http://169.254.169.254/ or http://localhost:6379 and the server reads it for you. So the
host must resolve only to public addresses, redirects are followed manually and
re-checked each hop, and the body is capped.
"""

import ipaddress
import re
import socket
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

MAX_BYTES = 512 * 1024
MAX_REDIRECTS = 4
TIMEOUT = 8.0


class FetchError(Exception):
    pass


def _check_public(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Only http(s) URLs can be saved")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise FetchError(f"Couldn't resolve {parsed.hostname}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FetchError("That address points to a private network and can't be fetched")


_TITLE_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title', re.I),
    re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S),
]
_AUTHOR = re.compile(r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)', re.I)


def parse_meta(html: str) -> tuple[str | None, str | None]:
    title = None
    for pattern in _TITLE_PATTERNS:
        m = pattern.search(html)
        if m and m.group(1).strip():
            title = " ".join(unescape(m.group(1)).split())[:500]
            break
    m = _AUTHOR.search(html)
    author = " ".join(unescape(m.group(1)).split())[:200] if m else None
    return title, author


def fetch_meta(url: str) -> tuple[str | None, str | None]:
    """(title, author) from the page, following up to MAX_REDIRECTS checked redirects."""
    with httpx.Client(
        timeout=TIMEOUT,
        follow_redirects=False,
        headers={"User-Agent": "Resurface/0.1 (+title fetch)"},
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _check_public(url)
            with client.stream("GET", url) as r:
                if r.is_redirect:
                    url = urljoin(url, r.headers.get("location", ""))
                    continue
                if r.status_code >= 400:
                    raise FetchError(f"The page returned HTTP {r.status_code}")
                if "html" not in r.headers.get("content-type", ""):
                    return None, None
                body = b""
                for chunk in r.iter_bytes():
                    body += chunk
                    if len(body) >= MAX_BYTES:
                        break
                return parse_meta(body.decode(r.encoding or "utf-8", errors="replace"))
    raise FetchError("Too many redirects")
