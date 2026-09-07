"""Cookie helpers that stay compatible with the standard-library CookieJar."""

from __future__ import annotations

from http.cookiejar import CookieJar
from http.cookies import SimpleCookie
from urllib.parse import urlsplit


def parse_set_cookie(value: str) -> dict[str, str]:
    """Parse a Set-Cookie header into its cookie name/value pairs."""
    parsed = SimpleCookie()
    parsed.load(value)
    return {key: morsel.value for key, morsel in parsed.items()}


def cookie_header(values: dict[str, str]) -> str:
    """Serialize simple cookie values for a request header."""
    return "; ".join(f"{key}={value}" for key, value in values.items())


def jar_snapshot(jar: CookieJar) -> dict[str, str]:
    """Return a safe name/value snapshot of a CookieJar."""
    return {cookie.name: cookie.value for cookie in jar}


def host_from_url(url: str) -> str:
    """Extract a hostname without exposing credentials or query parameters."""
    return urlsplit(url).hostname or ""