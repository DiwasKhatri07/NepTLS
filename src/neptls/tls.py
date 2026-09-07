"""TLS configuration and fingerprint inspection primitives.

NepTLS describes TLS settings and fingerprints for compatibility research. It
does not attempt to impersonate a browser or bypass access controls.
"""

from __future__ import annotations

import hashlib
import json
import socket
import ssl
from dataclasses import asdict, dataclass, field
from dataclasses import replace
from typing import Any


@dataclass(slots=True)
class TLSConfig:
    """A serializable TLS client configuration."""

    minimum_version: str = "TLSv1.2"
    maximum_version: str | None = None
    ciphers: tuple[str, ...] = ()
    alpn_protocols: tuple[str, ...] = ("http/1.1",)
    server_hostname: str | None = None
    verify: bool = True
    cafile: str | None = None
    certfile: str | None = None
    keyfile: str | None = None

    def _version(self, value: str) -> ssl.TLSVersion:
        names = {
            "TLSv1": "TLSv1",
            "TLSv1.1": "TLSv1_1",
            "TLSv1.2": "TLSv1_2",
            "TLSv1.3": "TLSv1_3",
        }
        try:
            return getattr(ssl.TLSVersion, names[value])
        except KeyError as exc:
            raise ValueError(f"Unsupported TLS version: {value}") from exc
        except AttributeError as exc:
            raise ValueError(f"Unsupported TLS version: {value}") from exc

    def ssl_context(self) -> ssl.SSLContext:
        context = ssl.create_default_context(cafile=self.cafile)
        context.minimum_version = self._version(self.minimum_version)
        if self.maximum_version:
            context.maximum_version = self._version(self.maximum_version)
        if not self.verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        if self.ciphers:
            context.set_ciphers(":".join(self.ciphers))
        if self.alpn_protocols:
            context.set_alpn_protocols(list(self.alpn_protocols))
        if self.certfile:
            context.load_cert_chain(self.certfile, self.keyfile)
        return context

    def for_transport(self, transport: str) -> "TLSConfig":
        """Return a copy advertising the ALPN required by a native transport."""
        normalized = transport.lower()
        protocol = {
            "http1": "http/1.1",
            "http2": "h2",
            "h3": "h3",
            "http3": "h3",
        }.get(normalized)
        if protocol is None:
            return self
        if protocol == "http/1.1":
            if self.alpn_protocols == ("http/1.1",):
                return self
            return replace(self, alpn_protocols=("http/1.1",))
        if protocol in self.alpn_protocols and self.alpn_protocols[0] == protocol:
            return self
        return replace(
            self,
            alpn_protocols=(protocol,) + tuple(
                value for value in self.alpn_protocols if value != protocol
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(slots=True)
class TLSFingerprint:
    """A comparable representation of negotiated TLS characteristics."""

    version: str = "TLSv1.3"
    cipher: str | None = None
    alpn: str | None = None
    server_name: str | None = None
    supported_groups: tuple[str, ...] = ()
    signature_algorithms: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()
    cipher_order: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @property
    def canonical(self) -> str:
        fields = (
            self.version,
            self.cipher or "",
            self.alpn or "",
            ",".join(self.supported_groups),
            ",".join(self.signature_algorithms),
            ",".join(self.extensions),
            ",".join(self.cipher_order),
        )
        return "|".join(fields)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical.encode()).hexdigest()

    def compare(self, other: "TLSFingerprint") -> bool:
        return self.canonical == other.canonical

    def diff(self, other: "TLSFingerprint") -> dict[str, tuple[Any, Any]]:
        left, right = self.to_dict(), other.to_dict()
        return {key: (left[key], right[key]) for key in left if left[key] != right[key]}

    @property
    def ja3_string(self) -> str:
        """Return a JA3-compatible field string for available local metadata."""
        return ",".join(
            (
                self.version.removeprefix("TLSv"),
                "-".join(self.cipher_order),
                "-".join(self.extensions),
                "-".join(self.supported_groups),
                "-".join(self.signature_algorithms),
            )
        )

    @property
    def ja3_hash(self) -> str:
        """Return the MD5 digest traditionally used for JA3 comparison."""
        return hashlib.md5(self.ja3_string.encode(), usedforsecurity=False).hexdigest()

    @classmethod
    def from_ssl_socket(cls, connection: ssl.SSLSocket) -> "TLSFingerprint":
        cipher = connection.cipher()
        return cls(
            version=connection.version() or "unknown",
            cipher=cipher[0] if cipher else None,
            alpn=connection.selected_alpn_protocol(),
            server_name=getattr(connection, "server_hostname", None),
            metadata={"source": "negotiated_socket"},
        )

    @classmethod
    def from_config(cls, config: TLSConfig) -> "TLSFingerprint":
        return cls(
            version=config.maximum_version or "TLSv1.3",
            alpn=config.alpn_protocols[0] if config.alpn_protocols else None,
            extensions=("server_name", "supported_versions", "signature_algorithms"),
            cipher_order=config.ciphers,
            metadata={"source": "configuration", "negotiated": False},
        )


def probe(host: str, port: int = 443, *, timeout: float = 10.0, server_hostname: str | None = None) -> TLSFingerprint:
    """Perform a verified TLS handshake and return negotiated properties."""
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=server_hostname or host) as secure:
            return TLSFingerprint.from_ssl_socket(secure)
