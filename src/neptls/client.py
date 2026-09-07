"""Synchronous requests-like HTTP client built on Python's standard library."""

from __future__ import annotations

import io
import gzip
import http.client
import json as json_module
import mimetypes
import random
import time
import zlib
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

from .exceptions import RequestError, TimeoutError, TransportUnavailableError
from .models import RequestTiming, Response
from .profiles import BrowserProfile, get_profile
from .tls import TLSConfig, TLSFingerprint
from .transports import (
    HTTP1,
    NativeResponse,
    create_transport,
    normalize_transport,
    transport_available,
)
from .urltools import build_url

AuthHook = Callable[[urllib.request.Request], None]


class BasicAuth:
    """Attach HTTP Basic authentication to a request."""

    def __init__(self, username: str, password: str) -> None:
        self.username, self.password = username, password

    def __call__(self, request: urllib.request.Request) -> None:
        import base64

        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode("ascii")
        request.add_unredirected_header("Authorization", f"Basic {token}")


class BearerAuth:
    """Attach a bearer token to a request without logging it."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: urllib.request.Request) -> None:
        request.add_unredirected_header("Authorization", f"Bearer {self.token}")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_: Any) -> None:
        return None


def _multipart(fields: Mapping[str, Any], files: Mapping[str, Any]) -> tuple[bytes, str]:
    boundary = f"----neptls-{random.randrange(10**12):012d}"
    buffer = io.BytesIO()
    for name, value in fields.items():
        buffer.write(f"--{boundary}\r\n".encode())
        buffer.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        buffer.write(str(value).encode())
        buffer.write(b"\r\n")
    for name, value in files.items():
        filename, content, content_type = name, value, None
        if isinstance(value, tuple):
            filename, content = value[0], value[1]
            content_type = value[2] if len(value) > 2 else None
        if hasattr(content, "read"):
            content = content.read()
        elif isinstance(content, (str, Path)) and Path(content).exists():
            path = Path(content)
            filename, content = filename or path.name, path.read_bytes()
        elif isinstance(content, str):
            content = content.encode()
        content_type = content_type or mimetypes.guess_type(str(filename))[0] or "application/octet-stream"
        buffer.write(f"--{boundary}\r\n".encode())
        buffer.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        buffer.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        buffer.write(content)
        buffer.write(b"\r\n")
    buffer.write(f"--{boundary}--\r\n".encode())
    return buffer.getvalue(), f"multipart/form-data; boundary={boundary}"


def _decode_content(content: bytes, encoding: str | None) -> bytes:
    if not encoding:
        return content
    try:
        if encoding.lower() == "gzip":
            return gzip.decompress(content)
        if encoding.lower() == "deflate":
            return zlib.decompress(content)
    except (OSError, zlib.error) as exc:
        raise RequestError(f"could not decode {encoding} response body") from exc
    return content


def _stdlib_http_version(raw: Any) -> str:
    version = getattr(raw, "version", 11)
    return {10: "HTTP/1.0", 11: "HTTP/1.1"}.get(version, "HTTP/1.1")


def _response_from_native(
    native: NativeResponse,
    *,
    method: str,
    transport: str,
    started: float,
) -> Response:
    return Response(
        status_code=native.status_code,
        reason=native.reason,
        url=native.url,
        headers=native.headers,
        content=native.content,
        request_method=method,
        timing=RequestTiming(started, time.perf_counter(), first_byte=time.perf_counter()),
        http_version=native.http_version,
        transport=transport,
    )


def _build_opener(
    *,
    cookies: CookieJar,
    tls_config: TLSConfig,
    proxy: str | None,
    follow_redirects: bool,
) -> urllib.request.OpenerDirector:
    handlers: list[Any] = [
        urllib.request.HTTPCookieProcessor(cookies),
        urllib.request.HTTPSHandler(context=tls_config.ssl_context()),
    ]
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    if not follow_redirects:
        handlers.append(_NoRedirect())
    return urllib.request.build_opener(*handlers)


class Client:
    """Reusable HTTP client with cookies, connection-aware opener, and retries."""

    def __init__(
        self,
        *,
        profile: str | BrowserProfile | None = None,
        impersonate: str | BrowserProfile | None = None,
        proxy: str | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: Mapping[str, str] | None = None,
        timeout: float = 30.0,
        verify: bool = True,
        follow_redirects: bool = True,
        retries: int = 0,
        backoff_factor: float = 0.2,
        transport: str = HTTP1,
        fallback_transport: str | None = None,
    ) -> None:
        if profile is not None and impersonate is not None:
            raise ValueError("pass either profile or impersonate, not both")
        profile = impersonate if impersonate is not None else profile
        self.profile = get_profile(profile)
        requested_transport = normalize_transport(transport)
        fallback = normalize_transport(fallback_transport) if fallback_transport is not None else None
        if fallback == requested_transport:
            raise ValueError("fallback_transport must differ from transport")
        self.requested_transport = requested_transport
        self.transport = requested_transport
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.retries = max(0, retries)
        self.backoff_factor = max(0.0, backoff_factor)
        self.cookies = CookieJar()
        self._headers = dict(self.profile.headers if self.profile else {})
        if self.profile:
            self._headers.setdefault("User-Agent", self.profile.user_agent)
        if headers:
            self._headers.update(headers)
        if cookies:
            for name, value in cookies.items():
                self.cookies.set_cookie(
                    __import__("http.cookiejar", fromlist=["Cookie"]).Cookie(
                        version=0,
                        name=name,
                        value=value,
                        port=None,
                        port_specified=False,
                        domain="",
                        domain_specified=False,
                        domain_initial_dot=False,
                        path="/",
                        path_specified=True,
                        secure=False,
                        expires=None,
                        discard=True,
                        comment=None,
                        comment_url=None,
                        rest={},
                        rfc2109=False,
                    )
                )
        if self.profile:
            tls_config = self.profile.tls
        else:
            tls_config = TLSConfig(verify=verify)
        if not verify:
            tls_config = TLSConfig(**{**tls_config.to_dict(), "verify": False})
        selected_tls_config = tls_config.for_transport(self.transport)
        self._opener = _build_opener(
            cookies=self.cookies,
            tls_config=selected_tls_config,
            proxy=proxy,
            follow_redirects=follow_redirects,
        )
        self._native_transport = None
        if self.transport != HTTP1:
            try:
                self._native_transport = create_transport(
                    self.transport,
                    verify=selected_tls_config.ssl_context()
                    if self.transport == "http2"
                    else selected_tls_config.verify,
                    headers=self._headers,
                    cookies=self.cookies,
                    proxy=proxy,
                    follow_redirects=follow_redirects,
                )
            except TransportUnavailableError:
                if fallback is None:
                    raise
                self.transport = fallback
                selected_tls_config = tls_config.for_transport(self.transport)
                self._opener = _build_opener(
                    cookies=self.cookies,
                    tls_config=selected_tls_config,
                    proxy=proxy,
                    follow_redirects=follow_redirects,
                )
                if fallback != HTTP1:
                    self._native_transport = create_transport(
                        fallback,
                        verify=selected_tls_config.ssl_context()
                        if fallback == "http2"
                        else selected_tls_config.verify,
                        headers=self._headers,
                        cookies=self.cookies,
                        proxy=proxy,
                        follow_redirects=follow_redirects,
                    )
        self.fallback_transport = fallback if self.transport != requested_transport else None
        self._tls_config = selected_tls_config
        self._last_protocol = "http/1.1" if self.transport == HTTP1 else None

    def _url(self, url: str, params: Mapping[str, Any] | None) -> str:
        return build_url(url, params)

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | str | None = None,
        json: Any = None,
        form: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        timeout: float | None = None,
        stream: bool = False,
        auth: AuthHook | None = None,
        decode_content: bool = True,
    ) -> Response:
        url = self._url(url, params)
        request_headers = dict(self._headers)
        if headers:
            request_headers.update(headers)
        request_headers.setdefault("Accept-Encoding", "gzip, deflate")
        body: bytes | None = None
        if json is not None:
            body = json_module.dumps(json).encode()
            request_headers.setdefault("Content-Type", "application/json")
        elif files:
            body, content_type = _multipart(form or {}, files)
            request_headers.setdefault("Content-Type", content_type)
        elif form is not None:
            body = urllib.parse.urlencode(form).encode()
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif data is not None:
            body = data.encode() if isinstance(data, str) else data
        if not decode_content:
            request_headers["Accept-Encoding"] = "identity"
        if auth:
            auth_request = urllib.request.Request(url, headers=request_headers, method=method.upper())
            auth(auth_request)
            request_headers.update(dict(auth_request.header_items()))
        if self._native_transport is not None:
            return self._request_native(
                method.upper(),
                url,
                headers=request_headers,
                body=body,
                timeout=timeout or self.timeout,
            )
        request = urllib.request.Request(url, data=body, headers=request_headers, method=method.upper())
        last_error: Exception | None = None
        retry_statuses = {429, 500, 502, 503, 504}
        for attempt in range(self.retries + 1):
            started = time.perf_counter()
            try:
                raw = self._opener.open(request, timeout=timeout or self.timeout)
                response = Response(
                    status_code=raw.status,
                    reason=raw.reason or "",
                    url=raw.geturl(),
                    headers=dict(raw.headers.items()),
                    raw=raw if stream else None,
                    content=b"" if stream else _decode_content(
                        raw.read(), raw.headers.get("Content-Encoding") if decode_content else None
                    ),
                    request_method=method.upper(),
                    timing=RequestTiming(started, time.perf_counter(), first_byte=time.perf_counter()),
                    http_version=_stdlib_http_version(raw),
                    transport=HTTP1,
                )
                if not stream:
                    raw.close()
                if response.status_code in retry_statuses and attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    continue
                return response
            except urllib.error.HTTPError as exc:
                response = Response(
                    status_code=exc.code,
                    reason=exc.reason or "",
                    url=exc.geturl(),
                    headers=dict(exc.headers.items()) if exc.headers else {},
                    raw=exc if stream else None,
                    content=b"" if stream else exc.read(),
                    request_method=method.upper(),
                    timing=RequestTiming(started, time.perf_counter(), first_byte=time.perf_counter()),
                    http_version=_stdlib_http_version(exc),
                    transport=HTTP1,
                )
                if not stream:
                    exc.close()
                if exc.code in retry_statuses and attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    continue
                return response
            except TimeoutError as exc:
                last_error = exc
                break
            except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    continue
                break
        if isinstance(last_error, TimeoutError):
            raise TimeoutError(f"request timed out: {url}") from last_error
        raise RequestError(f"request failed: {url}: {last_error}") from last_error

    def _request_native(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> Response:
        last_error: Exception | None = None
        retry_statuses = {429, 500, 502, 503, 504}
        for attempt in range(self.retries + 1):
            started = time.perf_counter()
            try:
                native = self._native_transport.request(
                    method,
                    url,
                    headers=headers,
                    body=body,
                    timeout=timeout,
                )
                response = _response_from_native(
                    native,
                    method=method,
                    transport=self.transport,
                    started=started,
                )
                self._last_protocol = response.protocol
                if response.status_code in retry_statuses and attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    continue
                return response
            except TimeoutError as exc:
                last_error = exc
                break
            except RequestError as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    continue
                break
        if isinstance(last_error, TimeoutError):
            raise TimeoutError(f"request timed out: {url}") from last_error
        raise RequestError(f"request failed: {url}: {last_error}") from last_error

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", url, **kwargs)

    def fingerprint(self) -> TLSFingerprint:
        return TLSFingerprint.from_config(self._tls_config)

    @property
    def protocol(self) -> str | None:
        """Return the last negotiated protocol, if a request was made."""
        return self._last_protocol

    @property
    def native_transport_available(self) -> bool:
        """Report whether this client's selected transport can be imported."""
        return transport_available(self.transport)

    def close(self) -> None:
        if self._native_transport is not None:
            self._native_transport.close()
            self._native_transport = None

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def request(method: str, url: str, **kwargs: Any) -> Response:
    client_keys = {
        "profile",
        "impersonate",
        "proxy",
        "headers",
        "cookies",
        "timeout",
        "verify",
        "follow_redirects",
        "retries",
        "backoff_factor",
        "transport",
        "fallback_transport",
    }
    client_options = {key: kwargs.pop(key) for key in tuple(kwargs) if key in client_keys}
    with Client(**client_options) as client:
        return client.request(method, url, **kwargs)


Session = Client


def get(url: str, **kwargs: Any) -> Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> Response:
    return request("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> Response:
    return request("PUT", url, **kwargs)


def patch(url: str, **kwargs: Any) -> Response:
    return request("PATCH", url, **kwargs)


def delete(url: str, **kwargs: Any) -> Response:
    return request("DELETE", url, **kwargs)


def head(url: str, **kwargs: Any) -> Response:
    return request("HEAD", url, **kwargs)


def options(url: str, **kwargs: Any) -> Response:
    return request("OPTIONS", url, **kwargs)
