"""Small, standard-library protocol encoding and hashing helpers."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote


def _bytes(value: str | bytes | bytearray) -> bytes:
    return value.encode() if isinstance(value, str) else bytes(value)


def sha256(value: str | bytes | bytearray) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def sha512(value: str | bytes | bytearray) -> str:
    return hashlib.sha512(_bytes(value)).hexdigest()


def blake2(value: str | bytes | bytearray, *, digest_size: int = 32) -> str:
    return hashlib.blake2b(_bytes(value), digest_size=digest_size).hexdigest()


def md5(value: str | bytes | bytearray) -> str:
    return hashlib.md5(_bytes(value), usedforsecurity=False).hexdigest()


def digest(value: str | bytes | bytearray, algorithm: str = "sha256") -> str:
    """Hash a value using any algorithm exposed by :mod:`hashlib`."""
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"unsupported hash algorithm: {algorithm}") from exc
    hasher.update(_bytes(value))
    return hasher.hexdigest()


def hash_file(path: str | Path, algorithm: str = "sha256", *, chunk_size: int = 131072) -> str:
    """Hash a file incrementally without loading it all into memory."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"unsupported hash algorithm: {algorithm}") from exc
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def b64encode(value: str | bytes | bytearray) -> str:
    return base64.b64encode(_bytes(value)).decode("ascii")


def b64decode(value: str | bytes) -> bytes:
    return base64.b64decode(_bytes(value))


def urlsafe_b64encode(value: str | bytes | bytearray) -> str:
    return base64.urlsafe_b64encode(_bytes(value)).decode("ascii").rstrip("=")


def urlsafe_b64decode(value: str | bytes) -> bytes:
    raw = _bytes(value)
    return base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4))


def base32encode(value: str | bytes | bytearray) -> str:
    return base64.b32encode(_bytes(value)).decode("ascii")


def base32decode(value: str | bytes) -> bytes:
    return base64.b32decode(_bytes(value))


def hex_encode(value: str | bytes | bytearray) -> str:
    return _bytes(value).hex()


def hex_decode(value: str) -> bytes:
    return bytes.fromhex(value)


def url_encode(value: str) -> str:
    return quote(value, safe="")


def url_decode(value: str) -> str:
    return unquote(value)


def json_encode(value: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def json_decode(value: str | bytes) -> Any:
    return json.loads(value)


def encode(value: str, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    return value.encode(encoding, errors)


def decode(value: bytes | bytearray, encoding: str = "utf-8", errors: str = "strict") -> str:
    return bytes(value).decode(encoding, errors)
