# Security Policy

NepTLS is a protocol research and HTTP client toolkit for authorized testing. It must not be used to attack systems, bypass access controls, steal sessions, guess credentials, or evade abuse controls.

## Reporting a vulnerability

Please do not open a public issue for an undisclosed vulnerability. Contact the maintainer privately through [@DiwasKhatri07](https://github.com/DiwasKhatri07) with the affected version, reproduction steps, impact, and mitigation details. Do not include real credentials, cookies, or private target data.

## Supported version

The current `0.4.x` release line receives priority for security fixes. Older versions are best effort.

## Scope notes

Browser profiles describe compatible metadata; they do not promise byte-identical browser TLS handshakes or a way around security controls. Optional HTTP/2 and HTTP/3 transports depend on their external backends and platform support.
