"""Read-only DNS, TCP, TLS, and HTTP diagnostics."""

from __future__ import annotations

import socket
import ssl
import time
from typing import Any
from urllib.parse import urlparse

from .client import Client
from .transports import normalize_transport


def inspect(
    url: str,
    *,
    timeout: float = 10.0,
    transport: str = "http1",
    fallback_transport: str | None = None,
) -> dict[str, Any]:
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    selected_transport = normalize_transport(transport)
    result: dict[str, Any] = {
        "url": url,
        "hostname": parsed.hostname,
        "port": port,
        "scheme": parsed.scheme,
        "dns": {},
        "tcp": {},
        "tls": {},
        "http": {},
    }
    dns_started = time.perf_counter()
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    result["dns"] = {
        "duration": time.perf_counter() - dns_started,
        "addresses": sorted({item[4][0] for item in addresses}),
    }
    tcp_started = time.perf_counter()
    with socket.create_connection((parsed.hostname, port), timeout=timeout) as raw:
        result["tcp"] = {"duration": time.perf_counter() - tcp_started, "connected": True}
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            if selected_transport == "http2":
                context.set_alpn_protocols(["h2", "http/1.1"])
            elif selected_transport == "http1":
                context.set_alpn_protocols(["http/1.1"])
            tls_started = time.perf_counter()
            with context.wrap_socket(raw, server_hostname=parsed.hostname) as secure:
                result["tls"] = {
                    "duration": time.perf_counter() - tls_started,
                    "version": secure.version(),
                    "cipher": secure.cipher()[0] if secure.cipher() else None,
                    "alpn": secure.selected_alpn_protocol(),
                    "peer_certificate": secure.getpeercert(),
                }
    client = Client(
        timeout=timeout,
        retries=0,
        transport=selected_transport,
        fallback_transport=fallback_transport,
    )
    response = client.head(url)
    result["http"] = {
        "status_code": response.status_code,
        "headers": response.headers,
        "http_version": response.http_version,
        "protocol": response.protocol,
        "transport": response.transport,
        "requested_transport": client.requested_transport,
        "fallback_transport": client.fallback_transport,
        "duration": response.timing.total if response.timing else None,
    }
    return result


diagnose = inspect
