# Changelog

All notable NepTLS changes are documented here. This project follows a
lightweight Keep a Changelog format and uses semantic versioning.

## [Unreleased]

Daily repository updates are collected here by the scheduled GitHub workflow.

## [0.4.1] — 2026-09-07

### Changed

- Refreshed the PyPI package metadata and public README.
- Added complete GitHub community health files and contributor guidance.
- Added CI, release, dependency, and daily changelog automation.
- Upgraded the live documentation website with stronger SEO, a polished visual
  system, improved release messaging, and a faster landing-page flow.

## [0.4.0] — 2026-09-06

### Added

- Optional native HTTP/2 transport through the `http2` extra.
- Optional native HTTP/3 transport through the `http3` extra.
- Explicit transport selectors, aliases, capability checks, and protocol metadata.
- Clear unavailable-backend errors with opt-in fallback behavior.
- Async transport selection and expanded transport regression coverage.

## [0.3.0] — 2026-09-05

### Added

- Chrome compatibility profiles and client hints.
- `impersonate="chrome"` request syntax.
- Diagnostics, crypto helpers, URL/cookie helpers, and response conveniences.

## [0.2.0] — 2026-09-04

### Added

- Browser profile metadata, user-agent helpers, retries, compression, auth hooks,
  streaming, multipart requests, pools, and CLI commands.

## [0.1.0] — 2026-09-03

### Added

- Standard-library HTTP client, async wrapper, TLS configuration, fingerprints,
  generic PoW, tests, and MIT licensing.

[Unreleased]: https://github.com/DiwasKhatri07/NepTLS/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.4.1
[0.4.0]: https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.4.0
[0.3.0]: https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.3.0
[0.2.0]: https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.2.0
[0.1.0]: https://github.com/DiwasKhatri07/NepTLS/releases/tag/v0.1.0