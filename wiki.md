# NepTLS Wiki

This is the practical reference for NepTLS 0.4.1. NepTLS is intentionally
small at runtime and uses Python's standard library by default. Optional
native HTTP/2 and HTTP/3 backends can be installed when a platform-tested
protocol implementation is required.

## Table of contents

1. [Install](#install)
2. [Quick start](#quick-start)
3. [curl-cffi-style syntax](#curl-cffi-style-syntax)
4. [Chrome compatibility profiles](#chrome-compatibility-profiles)
5. [HTTP methods and request data](#http-methods-and-request-data)
6. [Responses and errors](#responses-and-errors)
7. [Async requests](#async-requests)
8. [Native HTTP/2 and HTTP/3](#native-http2-and-http3)
9. [TLS and fingerprints](#tls-and-fingerprints)
10. [User-agent generation](#user-agent-generation)
11. [Cookies, URLs, and proxies](#cookies-urls-and-proxies)
12. [Hashing and encoding](#hashing-and-encoding)
13. [Generic proof of work](#generic-proof-of-work)
14. [Diagnostics and CLI](#diagnostics-and-cli)
15. [Security boundary](#security-boundary)

## Install

```powershell
python -m pip install --upgrade neptls
```

On Windows, always use the same Python executable for installation and
execution:

```powershell
$python = "C:\Path\To\python.exe"
& $python -m pip install --upgrade --force-reinstall --no-cache-dir neptls
& $python -c "import neptls; print(neptls.__version__, neptls.__file__)"
```

Do not name your own script `neptls.py`; that shadows the package.

## Quick start

```python
import neptls

response = neptls.get("https://example.com", timeout=10)
response.raise_for_status()
print(response.status_code)
print(response.text)
```

## curl-cffi-style syntax

The supported compatibility alias is `impersonate`. It selects a structured
NepTLS profile and its documented headers/TLS settings:

```python
import neptls

response = neptls.get(
    "https://example.com",
    impersonate="chrome",
    timeout=10,
)
```

Equivalent reusable form:

```python
client = neptls.Client(impersonate="chrome", retries=2)
response = client.get("https://example.com")
```

Supported names include:

```text
chrome
chrome-windows
chrome-macos
chrome-linux
chrome-android
firefox
edge
safari
```

`impersonate` does not promise browser byte-level TLS imitation and must not be
used to evade authentication, CAPTCHA, payment, or anti-abuse controls.

## Chrome compatibility profiles

Chrome profiles include:

- Chrome user-agent
- `Accept` and `Accept-Language`
- cache-control
- `Sec-CH-UA`
- `Sec-CH-UA-Mobile`
- `Sec-CH-UA-Platform`
- `Sec-Fetch-Dest`
- `Sec-Fetch-Mode`
- `Sec-Fetch-Site`
- `Sec-Fetch-User`
- `Upgrade-Insecure-Requests`
- ALPN preference metadata
- HTTP/2 settings metadata for research and comparison
- platform, language, timezone, screen, and hardware metadata

Inspect a profile without making a request:

```python
profile = neptls.get_profile("chrome-windows")
print(profile.to_json())
```

## HTTP methods and request data

```python
client = neptls.Client(timeout=20, retries=2)

client.get(url, params={"page": 1})
client.post(url, json={"name": "NepTLS"})
client.put(url, data="raw body")
client.patch(url, form={"enabled": "true"})
client.delete(url)
client.head(url)
client.options(url)
```

Multipart upload:

```python
client.post(
    url,
    form={"description": "report"},
    files={"document": ("report.txt", b"hello", "text/plain")},
)
```

Streaming:

```python
with client.get(url, stream=True) as response:
    for chunk in response.iter_content(65536):
        print(len(chunk))
```

Gzip and deflate are decoded by default. Disable decoding with
`decode_content=False`.

## Responses and errors

`Response` supports:

```python
response.status_code
response.reason
response.url
response.headers
response.content
response.text
response.json()
response.ok
response.elapsed
response.is_redirect
response.is_client_error
response.is_server_error
response.links
response.iter_bytes()
response.iter_lines()
response.raise_for_status()
response.close()
```

Exceptions:

```python
try:
    response.raise_for_status()
except neptls.HTTPStatusError as error:
    print(error.response.status_code)
except neptls.RequestError as error:
    print(error)
```

Retries apply to common temporary statuses (`429`, `500`, `502`, `503`,
`504`) and malformed/transient transport exceptions when configured.

## Async requests

```python
import asyncio
import neptls

async def main():
    async with neptls.AsyncClient(impersonate="chrome") as client:
        response = await client.get("https://example.com")
        print(response.status_code)

asyncio.run(main())
```


## Native HTTP/2 and HTTP/3

The default `http1` transport remains dependency-free. Select an optional
native transport explicitly on either client:

```powershell
python -m pip install "neptls[http2]"
python -m pip install "neptls[http3]"
```

```python
with neptls.Client(transport="http2") as client:
    response = client.get("https://example.com")
    print(response.http_version)  # negotiated HTTP/2
    print(response.protocol)      # h2
```

HTTP/2 uses a persistent `httpx` client with the `h2` extension, so requests
made through the same `Client` can reuse connections. HTTP/3 uses
`curl-cffi`'s native QUIC mode. The HTTP/3 wheel must be built with libcurl
HTTP/3 support; installing the extra alone does not add QUIC support to a
platform build that lacks it.

`AsyncClient` accepts the same `transport` selector and exposes the same
response metadata:

```python
async with neptls.AsyncClient(transport="http2") as client:
    response = await client.get("https://example.com")
    print(response.negotiated_protocol)
```

Selecting an unavailable native backend raises
`TransportUnavailableError` rather than silently pretending that the request
used HTTP/1.1. If an application prefers an explicit downgrade, opt into it:

```python
client = neptls.Client(transport="http2", fallback_transport="http1")
```

The response reports the actual negotiated protocol through `http_version`,
`protocol`, and `negotiated_protocol`. `neptls.transport_available("http2")`
and `neptls.transport_available("http3")` can be used for capability checks.

## TLS and fingerprints

```python
config = neptls.TLSConfig(
    minimum_version="TLSv1.2",
    alpn_protocols=("h2", "http/1.1"),
    verify=True,
)

fingerprint = neptls.TLSFingerprint.from_config(config)
print(fingerprint.canonical)
print(fingerprint.digest)
print(fingerprint.ja3_string)
print(fingerprint.ja3_hash)
```

Probe negotiated endpoint properties:

```python
negotiated = neptls.probe_tls("example.com")
print(negotiated.version)
print(negotiated.cipher)
print(negotiated.alpn)
```

Configuration fingerprints are estimates; negotiated fingerprints require an
actual TLS socket. NepTLS exposes inspection and comparison, not ClientHello
spoofing.

## User-agent generation

```python
neptls.ua.random()
neptls.ua.chrome()
neptls.ua.firefox()
neptls.ua.edge()
neptls.ua.safari()
neptls.ua.mobile()

neptls.user_agents.parse(neptls.ua.random())
neptls.ua.filter(browser="chrome", platform="windows")
```

Generate a consistent local test profile:

```python
profile = neptls.fingerprint.generate(
    browser="chrome",
    platform="windows",
    seed=42,
)
profile.validate()
print(profile.to_dict())
```

## Cookies, URLs, and proxies

```python
from neptls.cookies import cookie_header, parse_set_cookie
from neptls.urltools import build_url, normalize_url, query_params

print(normalize_url("example.com/path"))
print(build_url("https://example.com?a=1", {"b": "2"}))
print(query_params("https://example.com?a=1"))
print(parse_set_cookie("session=abc; Path=/"))
print(cookie_header({"session": "abc"}))
```

```python
client = neptls.Client(
    proxy="http://127.0.0.1:8080",
    cookies={"session": "local-test"},
)
```

Proxy credentials should be supplied through a secure runtime configuration,
not committed into source code.

## Hashing and encoding

```python
from neptls import crypto

crypto.sha256("hello")
crypto.sha512("hello")
crypto.blake2("hello")
crypto.digest("hello", "sha3_256")
crypto.hash_file("payload.bin")
crypto.b64encode("hello")
crypto.b64decode("aGVsbG8=")
crypto.urlsafe_b64encode("hello")
crypto.urlsafe_b64decode("aGVsbG8")
crypto.base32encode("hello")
crypto.base32decode("NBSWY3DP")
crypto.hex_encode("hello")
crypto.hex_decode("68656c6c6f")
crypto.url_encode("hello world")
crypto.url_decode("hello%20world")
crypto.json_encode({"ok": True})
crypto.json_decode('{"ok": true}')
crypto.encode("hello")
crypto.decode(b"hello")
```

## Generic proof of work

```python
from neptls.pow import Challenge, benchmark, solve, solve_parallel, verify

challenge = Challenge("research payload", difficulty=3, algorithm="sha256")
result = solve(challenge)
assert verify(challenge, result.nonce)

parallel = solve_parallel(challenge, workers=4)
print(parallel.digest)
print(benchmark(challenge, attempts=1000))
```

The PoW module is generic. It does not implement a solver for any named
anti-abuse, CAPTCHA, login, payment, or access-control system.

## Diagnostics and CLI

```python
report = neptls.inspect("https://example.com")
print(report["dns"])
print(report["tcp"])
print(report["tls"])
print(report["http"])
```

```powershell
neptls version
neptls get https://example.com
neptls get https://example.com --header "Accept: application/json"
neptls inspect https://example.com
neptls profile chrome-windows
neptls ua mobile
neptls hash "hello" --algorithm sha256
neptls pow demo --difficulty 3
```

## Security boundary

Use NepTLS only for systems you own or are authorized to test. The project
does not provide or document credential attacks, session theft, CAPTCHA
solving, payment-security bypass, authentication bypass, or anti-abuse
evasion.
