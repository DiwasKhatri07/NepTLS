"""Proxy configuration and health tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(slots=True)
class Proxy:
    url: str
    failures: int = 0
    requests: int = 0
    last_error: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https", "socks4", "socks5"} or not parsed.netloc:
            raise ValueError("proxy URL must include a supported scheme and host")

    @property
    def redacted(self) -> str:
        parsed = urlparse(self.url)
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme}://{host}{port}"

    def record_success(self) -> None:
        self.requests += 1

    def record_failure(self, error: Exception | str) -> None:
        self.requests += 1
        self.failures += 1
        self.last_error = str(error)
