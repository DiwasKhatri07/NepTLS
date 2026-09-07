# Contributing to NepTLS

## Setup

```bash
git clone https://github.com/DiwasKhatri07/NepTLS.git
cd NepTLS
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

NepTLS has zero core runtime dependencies. Optional transports can be installed with `python -m pip install -e '.[native]'`.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m compileall -q src
```

## Pull requests

Keep changes focused, update documentation for public API changes, include a regression test where practical, and explain any security or compatibility implications. Never commit credentials, captured cookies, private network data, or generated build artifacts.

NepTLS is intended for systems you own or are authorized to test. Contributions must not add credential attacks, access-control bypasses, CAPTCHA solving, or anti-abuse evasion features.
