"""Small URL and query-string helpers used by HTTP clients and integrations."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def build_url(url: str, params: Mapping[str, object] | None = None) -> str:
    """Append query parameters while preserving existing query values."""
    if not params:
        return url
    parsed = urlsplit(url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    query.extend((key, str(value)) for key, value in params.items())
    return urlunsplit(parsed._replace(query=urlencode(query)))


def normalize_url(url: str, *, default_scheme: str = "https") -> str:
    """Add a scheme to a host-like URL and remove surrounding whitespace."""
    value = url.strip()
    if "://" not in value:
        value = f"{default_scheme}://{value}"
    parsed = urlsplit(value)
    if not parsed.hostname:
        raise ValueError(f"invalid URL: {url!r}")
    return urlunsplit(parsed)


def query_params(url: str) -> dict[str, str]:
    """Return the first value for each query parameter."""
    return {key: value for key, value in parse_qsl(urlsplit(url).query, keep_blank_values=True)}