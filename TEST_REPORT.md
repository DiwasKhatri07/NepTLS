# NepTLS 0.4.1 Test Report

## Scope

This report covers the user-provided Windows run log, the original 0.1.0
regression suite, the 0.2.0 feature additions, and the 0.3.0 compatibility
profile additions.

## Issues found in the attached log

| Count | Result | Issue |
| ---: | --- | --- |
| 1 | User-side fix documented | `NameError: neptls is not defined` came from a missing `import neptls`. |
| 1 | User-side fix documented | A local file named `neptls.py` shadowed the installed package. |
| 1 | Fixed in 0.2.0 | `BadStatusLine` network failures were not normalized into `RequestError` or retried. |
| 1 | Fixed in 0.2.0 | `neptls.ua.chrome()` was documented but unavailable on the exported UA database object. |
| 4 | Already successful | HTTP 200, TLS/profile serialization, fingerprint generation, pool rotation, and hashing worked. |

The `BadStatusLine: ÿÿÿ` event is treated as a malformed/transient HTTP
transport failure. NepTLS now catches the standard-library HTTP exception and
reports a stable `RequestError`; configured retries can retry it. It cannot
make a broken remote proxy or server return a valid HTTP response.

## Automated results

```text
13 tests passed
0 failures
0 errors
```

Coverage includes synchronous and asynchronous requests, JSON POST bodies,
query parameters, profiles, TLS fingerprint comparison, UA parsing and
helpers, gzip decoding, Basic/Bearer auth hooks, hashing/encoding round trips,
parallel SHA-512 PoW, and PoW benchmarking.

## Security boundary

The 0.3.0 release adds compatibility and diagnostics primitives only. It does not
add CAPTCHA solving, authentication bypass, credential attacks, payment
security bypasses, session theft, or anti-abuse evasion.