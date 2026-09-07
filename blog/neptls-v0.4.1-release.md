# NepTLS v0.4.1: clear, inspectable HTTP and TLS tooling for Python

**Published:** September 7, 2026  
**Release:** [`neptls` 0.4.1](https://pypi.org/project/neptls/)

NepTLS v0.4.1 is now available on PyPI. It is a dependency-light HTTP client and TLS research toolkit for engineers who need protocol visibility, explicit transport behavior, and an auditable Python API.

> **Authorized use only:** NepTLS is designed for systems you own or are explicitly authorized to test. It is not an access-control bypass, credential attack, CAPTCHA solver, or anti-abuse evasion tool.

## Install

```bash
python -m pip install --upgrade neptls
```

Optional native transports are available when your platform supports them:

```bash
python -m pip install "neptls[http2]"
python -m pip install "neptls[http3]"
python -m pip install "neptls[native]"
```

## What is new in 0.4.1?

This release brings the NepTLS package to a polished, public release surface. The client now has clearer PyPI metadata, explicit project links, complete community health files, stronger documentation, and release automation around the package's existing HTTP, TLS, diagnostics, and optional native transport capabilities.

The v0.4.x line includes explicit HTTP/2 and HTTP/3 transport selection, capability checks, asynchronous transport support, Chrome-compatible request profiles, TLS inspection helpers, diagnostics, user-agent utilities, hashing, generic proof-of-work primitives, and a command-line interface.

## A small example

```python
import neptls

response = neptls.get(
    "https://example.com",
    impersonate="chrome",
    timeout=10,
)

response.raise_for_status()
print(response.status_code, response.http_version)
```

For explicit protocol selection:

```python
from neptls import Client, transport_available

transport = "http2" if transport_available("http2") else "http1"
client = Client(transport=transport)
response = client.get("https://example.com")

print(response.http_version)
print(response.timing.total)
```

NepTLS does not silently downgrade a requested native transport. If a selected backend is unavailable, it raises `TransportUnavailableError` unless fallback behavior is explicitly requested.

## Why NepTLS?

NepTLS keeps its core dependency-free and inspectable. That makes it practical for teaching, protocol experiments, diagnostics, compatibility testing, defensive automation, and controlled internal tooling. Optional backends can be added when HTTP/2 or HTTP/3 support is required, without making the default installation heavier than necessary.

The project also keeps its security boundary explicit. Browser profiles represent compatible headers and metadata; they do not promise byte-identical browser ClientHello generation or a way around a security control. The TLS helpers are for observation and configuration, not stealth.

## Project links

- **Install:** [PyPI — neptls](https://pypi.org/project/neptls/)
- **Source:** [github.com/DiwasKhatri07/NepTLS](https://github.com/DiwasKhatri07/NepTLS)
- **Release:** [NepTLS v0.4.1](https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.4.1)
- **Issues:** [GitHub Issues](https://github.com/DiwasKhatri07/NepTLS/issues)
- **Maintainer:** [Diwas Khatri](https://github.com/DiwasKhatri07)

## Contributing

Contributions are welcome. Read the [contributing guide](../../CONTRIBUTING.md), [security policy](../../SECURITY.md), and [code of conduct](../../CODE_OF_CONDUCT.md) before opening a pull request. Please include tests, documentation, and a clear explanation of the authorized-use and compatibility impact of protocol changes.

Thank you to everyone testing the package, reporting edge cases, and helping make Python networking tools more transparent.
