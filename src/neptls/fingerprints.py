"""Structured local fingerprint profiles for compatibility diagnostics."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from typing import Any

from .profiles import PROFILES


@dataclass(slots=True)
class ClientFingerprint:
    browser: str
    os: str
    language: str
    timezone: str
    resolution: tuple[int, int]
    platform: str
    touch: bool
    cores: int
    user_agent: str
    device: str = "desktop"
    webgl: dict[str, str] = field(default_factory=dict)
    fonts: tuple[str, ...] = ()
    networking: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "ClientFingerprint":
        if self.browser not in PROFILES:
            raise ValueError(f"unsupported browser profile: {self.browser}")
        if self.resolution[0] <= 0 or self.resolution[1] <= 0 or self.cores <= 0:
            raise ValueError("resolution and cores must be positive")
        if self.device == "mobile" and not self.touch:
            raise ValueError("mobile profiles must advertise touch capability")
        return self

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["resolution"] = list(self.resolution)
        value["fonts"] = list(self.fonts)
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def compare(self, other: "ClientFingerprint") -> bool:
        return self.to_dict() == other.to_dict()

    def diff(self, other: "ClientFingerprint") -> dict[str, tuple[Any, Any]]:
        left, right = self.to_dict(), other.to_dict()
        return {key: (left[key], right[key]) for key in left if left[key] != right[key]}


def generate(*, browser: str = "chrome", platform: str = "windows", seed: int | None = None) -> ClientFingerprint:
    if browser not in PROFILES:
        raise ValueError(f"unknown browser {browser!r}; choose from {sorted(PROFILES)}")
    profile = PROFILES[browser]
    rng = random.Random(seed)
    mobile_device = platform in {"android", "ios"}
    fingerprint = ClientFingerprint(
        browser=browser,
        os=platform,
        language=profile.language,
        timezone=profile.timezone,
        resolution=(390, 844) if mobile_device else (1920, 1080),
        platform=platform,
        touch=mobile_device,
        cores=4 if mobile_device else rng.choice((4, 8, 12)),
        user_agent=profile.user_agent,
        device="mobile" if mobile_device else "desktop",
        webgl={"vendor": "Research profile", "renderer": "Not collected"},
        fonts=("Arial", "sans-serif"),
        networking={"alpn": list(profile.tls.alpn_protocols)},
    )
    return fingerprint.validate()
