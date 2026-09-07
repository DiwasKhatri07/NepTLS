"""Optional native HTTP transport backends.

The standard library is deliberately kept as NepTLS's default HTTP/1.1
transport.  Native HTTP/2 and HTTP/3 are loaded only when the caller selects
them and their optional platform dependencies are installed.
"""

from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Any, Mapping

from .exceptions import RequestError, TransportUnavailableError

HTTP1 = "http1"
HTTP2 = "http2"
HTTP3 = "http3"
SUPPORTED_TRANSPORTS = (HTTP1, HTTP2, HTTP3)


def normalize_transport(value: str | None) -> str:
    """Normalize the public transport selector and reject unknown values."""
    aliases = {
        None: HTTP1,
        HTTP1: HTTP1,
        HTTP2: HTTP2,
        HTTP3: HTTP3,
        "1": HTTP1,
        "1.1": HTTP1,
        "http/1.1": HTTP1,
        "h1": HTTP1,
        "2": HTTP2,
        "h2": HTTP2,
        "http/2": HTTP2,
        "3": HTTP3,
        "h3": HTTP3,
        "http/3": HTTP3,
    }
    normalized = aliases.get(value.lower() if isinstance(value, str) else value)
    if normalized is None:
        supported = ", ".join(SUPPORTED_TRANSPORTS)
        raise ValueError(f"unsupported transport {value!r}; choose one of: {supported}")
    return normalized


def _optional_import_error(name: str, package: str, extra: str, detail: str = "") -> TransportUnavailableError:
    suffix = f" ({detail})" if detail else ""
    return TransportUnavailableError(
        f"{name} transport is unavailable{suffix}; install the optional dependency "
        f"with `python -m pip install neptls[{extra}]`"
    )


def transport_available(transport: str) -> bool:
    """Return whether an optional transport backend can be imported."""
    normalized = normalize_transport(transport)
    if normalized == HTTP1:
        return True
    if normalized == HTTP2:
        try:
            import httpx  # noqa: F401
            import h2  # noqa: F401
        except (ImportError, OSError):
            return False
        return True
    try:
        from curl_cffi import CurlHttpVersion  # noqa: F401
        from curl_cffi import requests as curl_requests  # noqa: F401
    except (ImportError, OSError):
        return False
    return _curl_http_version("http3") is not None


@dataclass(slots=True)
class NativeResponse:
    """Small response shape shared by optional backends."""

    status_code: int
    reason: str
    url: str
    headers: dict[str, str]
    content: bytes
    http_version: str


def _normalize_http_version(value: Any, requested: str) -> str:
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="replace")
    text = str(value or "").upper().replace("_", "/")
    if "3" in text:
        return "HTTP/3"
    if "2" in text:
        return "HTTP/2"
    if "1.0" in text:
        return "HTTP/1.0"
    if "1.1" in text:
        return "HTTP/1.1"
    return {"http2": "HTTP/2", "http3": "HTTP/3"}.get(requested, "HTTP/1.1")


def _curl_http_version(transport: str) -> Any:
    try:
        from curl_cffi import CurlHttpVersion
    except ImportError:
        return None
    names = ("V3", "V3_0") if transport == HTTP3 else ("V2_0", "V2")
    for name in names:
        version = getattr(CurlHttpVersion, name, None)
        if version is not None:
            return version
    return None


class HTTPXTransport:
    """Persistent HTTP/2 transport backed by httpx and hyper-h2."""

    def __init__(
        self,
        *,
        verify: bool | ssl.SSLContext,
        headers: Mapping[str, str],
        cookies: Any,
        proxy: str | None,
        follow_redirects: bool,
    ) -> None:
        try:
            import httpx
            import h2  # noqa: F401
        except (ImportError, OSError) as exc:
            raise _optional_import_error("HTTP/2", "httpx[http2]", "http2") from exc

        options: dict[str, Any] = {
            "http2": True,
            "verify": verify,
            "headers": dict(headers),
            "cookies": cookies,
            "follow_redirects": follow_redirects,
        }
        if proxy:
            options["proxy"] = proxy
        try:
            self._client = httpx.Client(**options)
        except TypeError:
            # httpx versions before 0.26 called this option ``proxies``.
            if proxy:
                options.pop("proxy", None)
                options["proxies"] = proxy
            self._client = httpx.Client(**options)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> NativeResponse:
        try:
            response = self._client.request(
                method,
                url,
                headers=dict(headers),
                content=body,
                timeout=timeout,
            )
            return NativeResponse(
                status_code=response.status_code,
                reason=response.reason_phrase or "",
                url=str(response.url),
                headers=dict(response.headers.items()),
                content=response.content,
                http_version=_normalize_http_version(response.http_version, HTTP2),
            )
        except Exception as exc:
            raise RequestError(f"HTTP/2 request failed: {exc}") from exc

    def close(self) -> None:
        self._client.close()


class CurlHTTP3Transport:
    """Persistent HTTP/3 transport backed by curl-cffi's native QUIC stack."""

    def __init__(
        self,
        *,
        verify: bool,
        headers: Mapping[str, str],
        cookies: Any,
        proxy: str | None,
        follow_redirects: bool,
    ) -> None:
        try:
            from curl_cffi import requests as curl_requests
        except (ImportError, OSError) as exc:
            raise _optional_import_error("HTTP/3", "curl-cffi", "http3") from exc
        self._http_version = _curl_http_version(HTTP3)
        if self._http_version is None:
            raise _optional_import_error(
                "HTTP/3",
                "curl-cffi",
                "http3",
                "the installed libcurl was built without HTTP/3/QUIC support",
            )

        options: dict[str, Any] = {
            "verify": verify,
            "headers": dict(headers),
            "cookies": cookies,
            "allow_redirects": follow_redirects,
        }
        if proxy:
            options["proxies"] = {"http": proxy, "https": proxy}
        try:
            self._session = curl_requests.Session(**options)
        except TypeError:
            options.pop("allow_redirects", None)
            options.pop("cookies", None)
            self._session = curl_requests.Session(**options)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> NativeResponse:
        if not url.lower().startswith("https://"):
            raise RequestError("HTTP/3 requires an https:// URL")
        try:
            response = self._session.request(
                method,
                url,
                headers=dict(headers),
                data=body,
                timeout=timeout,
                http_version=self._http_version,
            )
            return NativeResponse(
                status_code=response.status_code,
                reason=getattr(response, "reason", "") or "",
                url=str(response.url),
                headers=dict(response.headers.items()),
                content=bytes(response.content),
                http_version=_normalize_http_version(
                    getattr(response, "http_version", None), HTTP3
                ),
            )
        except Exception as exc:
            raise RequestError(f"HTTP/3 request failed: {exc}") from exc

    def close(self) -> None:
        self._session.close()


def create_transport(
    transport: str,
    *,
    verify: bool | ssl.SSLContext,
    headers: Mapping[str, str],
    cookies: Any,
    proxy: str | None,
    follow_redirects: bool,
) -> HTTPXTransport | CurlHTTP3Transport:
    """Create an optional backend; HTTP/1.1 intentionally uses urllib."""
    normalized = normalize_transport(transport)
    if normalized == HTTP2:
        return HTTPXTransport(
            verify=verify,
            headers=headers,
            cookies=cookies,
            proxy=proxy,
            follow_redirects=follow_redirects,
        )
    if normalized == HTTP3:
        if isinstance(verify, ssl.SSLContext):
            verify = True
        return CurlHTTP3Transport(
            verify=bool(verify),
            headers=headers,
            cookies=cookies,
            proxy=proxy,
            follow_redirects=follow_redirects,
        )
    raise ValueError("HTTP/1.1 uses the standard-library transport")