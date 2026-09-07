# NepTLS API Guide

This guide is a compact reference for the public 0.2.0 API.

## HTTP

```python
import neptls

neptls.get(url, params=None, headers=None, timeout=30)
neptls.post(url, json=data)
neptls.request("OPTIONS", url)
neptls.Client(profile="chrome", retries=2)
neptls.AsyncClient(timeout=10)
```

`Response` exposes `status_code`, `reason`, `url`, `headers`, `content`,
`text`, `json()`, `ok`, `history`, `timing`, `iter_bytes()`, `iter_lines()`,
`raise_for_status()`, and `close()`.

## TLS

- `TLSConfig` serializes TLS versions, ciphers, ALPN, verification, CA files,
  and client certificates.
- `TLSFingerprint.from_config(config)` describes local settings.
- `neptls.probe_tls(host)` performs a verified handshake and reports negotiated
  version, cipher, ALPN, and source metadata.
- `TLSFingerprint.ja3_string` and `.ja3_hash` provide a comparison string for
  the metadata available locally. They are not a browser impersonation engine.

## User agents and profiles

`neptls.ua.random()`, `.chrome()`, `.firefox()`, `.edge()`, `.safari()`, and
`.mobile()` select from the curated catalog. `UserAgentDatabase` accepts a
caller-owned, properly licensed iterable of strings.

`neptls.fingerprint.generate()` produces an internally validated, serializable
local test profile. It should not be used to defeat access controls.

## Crypto and proof of work

`neptls.crypto` includes SHA-256, SHA-512, BLAKE2, MD5 compatibility,
arbitrary hashlib algorithms, incremental file hashing, Base64/Base32,
URL-safe Base64, hex, URL encoding, JSON, and bytes/string conversion.

`neptls.pow.Challenge` accepts a payload, difficulty, and hashlib algorithm.
Use `solve()`, `solve_parallel()`, `verify()`, and `benchmark()` for generic
protocol research.

## Errors

- `NepTLSError`: package base exception.
- `RequestError`: a request could not be completed.
- `TimeoutError`: a request exceeded its timeout.
- `HTTPStatusError`: `Response.raise_for_status()` found a 4xx/5xx response.
- `InvalidProfileError`: a profile failed validation.
- `PowError`: a generic PoW challenge is invalid or unsolved.