"""Public response and timing models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

from .exceptions import HTTPStatusError


@dataclass(slots=True)
class RequestTiming:
    """Durations measured while a response was received."""

    started_at: float
    completed_at: float
    dns: float | None = None
    connect: float | None = None
    tls: float | None = None
    first_byte: float | None = None

    @property
    def total(self) -> float:
        return self.completed_at - self.started_at


class Response:
    """A requests-like HTTP response with explicit, inspectable state."""

    def __init__(
        self,
        *,
        status_code: int,
        reason: str,
        url: str,
        headers: dict[str, str],
        content: bytes = b"",
        raw: Any = None,
        request_method: str = "GET",
        history: tuple["Response", ...] = (),
        timing: RequestTiming | None = None,
        http_version: str = "HTTP/1.1",
        transport: str = "http1",
    ) -> None:
        self.status_code = status_code
        self.reason = reason
        self.url = url
        self.headers = {key.lower(): value for key, value in headers.items()}
        self._content = content
        self._raw = raw
        self.request_method = request_method
        self.history = history
        self.timing = timing
        self.http_version = http_version
        self.transport = transport

    @property
    def content(self) -> bytes:
        if self._raw is not None and not self._content:
            self._content = self._raw.read()
            self.close()
        return self._content

    @property
    def text(self) -> str:
        encoding = self.encoding or "utf-8"
        return self.content.decode(encoding, errors="replace")

    @property
    def encoding(self) -> str | None:
        content_type = self.headers.get("content-type", "")
        for part in content_type.split(";")[1:]:
            name, _, value = part.strip().partition("=")
            if name.lower() == "charset" and value:
                return value.strip("\"'")
        return None

    @property
    def charset(self) -> str | None:
        return self.encoding

    @property
    def elapsed(self) -> float | None:
        return self.timing.total if self.timing else None

    @property
    def protocol(self) -> str:
        """Return the negotiated protocol token used by diagnostics."""
        return {
            "HTTP/1.0": "http/1.0",
            "HTTP/1.1": "http/1.1",
            "HTTP/2": "h2",
            "HTTP/3": "h3",
        }.get(self.http_version, self.http_version.lower())

    @property
    def negotiated_protocol(self) -> str:
        """Alias for :attr:`protocol` for explicit transport diagnostics."""
        return self.protocol

    @property
    def is_redirect(self) -> bool:
        return self.status_code in {301, 302, 303, 307, 308}

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        return self.status_code >= 500

    @property
    def links(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in self.headers.get("link", "").split(","):
            target, _, attributes = item.partition(";")
            target = target.strip().strip("<>")
            for attribute in attributes.split(";"):
                name, _, value = attribute.strip().partition("=")
                if name.lower() == "rel" and value:
                    result[value.strip('"')] = target
        return result

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self) -> Any:
        return json.loads(self.text)

    def iter_bytes(self, chunk_size: int = 65536) -> Iterator[bytes]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if self._raw is not None:
            while True:
                chunk = self._raw.read(chunk_size)
                if not chunk:
                    self.close()
                    break
                yield chunk
            return
        for index in range(0, len(self._content), chunk_size):
            yield self._content[index : index + chunk_size]

    def iter_content(self, chunk_size: int = 65536) -> Iterator[bytes]:
        return self.iter_bytes(chunk_size)

    def iter_lines(self) -> Iterator[str]:
        for line in self.content.splitlines():
            yield line.decode(self.encoding or "utf-8", errors="replace")

    def raise_for_status(self) -> "Response":
        if not self.ok:
            raise HTTPStatusError(
                f"{self.request_method} {self.url} returned {self.status_code} {self.reason}",
                self,
            )
        return self

    def close(self) -> None:
        if self._raw is not None:
            self._raw.close()
            self._raw = None

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}] {self.url!r}>"
