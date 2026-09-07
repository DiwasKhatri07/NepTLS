"""Validated browser/network profile data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .exceptions import InvalidProfileError
from .tls import TLSConfig
from .user_agents import chrome, firefox, mobile


@dataclass(slots=True)
class BrowserProfile:
    name: str
    browser: str
    version: str
    platform: str
    user_agent: str
    language: str = "en-US"
    timezone: str = "UTC"
    screen: dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    hardware: dict[str, Any] = field(default_factory=lambda: {"cores": 8, "memory_gb": 16, "touch": False})
    headers: dict[str, str] = field(default_factory=dict)
    tls: TLSConfig = field(default_factory=TLSConfig)
    http2: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "BrowserProfile":
        if not self.name or not self.browser or not self.user_agent:
            raise InvalidProfileError("profile name, browser, and user_agent are required")
        if self.screen["width"] <= 0 or self.screen["height"] <= 0:
            raise InvalidProfileError("screen dimensions must be positive")
        return self

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["tls"] = self.tls.to_dict()
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BrowserProfile":
        data = dict(value)
        tls_data = data.pop("tls", {})
        data["tls"] = TLSConfig(**tls_data)
        return cls(**data).validate()


def _profile(name: str, browser: str, version: str, platform: str, user_agent: str) -> BrowserProfile:
    is_chrome = browser == "chrome"
    platform_hint = {
        "windows": '"Windows"',
        "macos": '"macOS"',
        "linux": '"Linux"',
        "android": '"Android"',
    }.get(platform, f'"{platform}"')
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if is_chrome:
        headers.update(
            {
                "Cache-Control": "max-age=0",
                "Sec-CH-UA": f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not_A Brand";v="99"',
                "Sec-CH-UA-Mobile": "?0" if platform not in {"android", "ios"} else "?1",
                "Sec-CH-UA-Platform": platform_hint,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
        )
    return BrowserProfile(
        name=name,
        browser=browser,
        version=version,
        platform=platform,
        user_agent=user_agent,
        headers=headers,
        tls=TLSConfig(alpn_protocols=("h2", "http/1.1")),
        http2={"header_table_size": 65536, "enable_push": 0, "initial_window_size": 6291456},
    )


PROFILES = {
    "chrome": _profile("chrome", "chrome", "131", "windows", chrome()),
    "chrome-windows": _profile("chrome-windows", "chrome", "131", "windows", chrome()),
    "chrome-macos": _profile("chrome-macos", "chrome", "131", "macos", chrome()),
    "chrome-linux": _profile("chrome-linux", "chrome", "131", "linux", chrome()),
    "chrome-android": _profile("chrome-android", "chrome", "131", "android", mobile()),
    "firefox": _profile("firefox", "firefox", "133", "linux", firefox()),
    "edge": _profile("edge", "edge", "131", "windows", chrome()),
    "safari": _profile("safari", "safari", "18.1", "macos", mobile()),
}


def get_profile(value: str | BrowserProfile | None) -> BrowserProfile | None:
    if value is None:
        return None
    if isinstance(value, BrowserProfile):
        return value.validate()
    try:
        return BrowserProfile.from_dict(PROFILES[value.lower()].to_dict())
    except KeyError as exc:
        raise InvalidProfileError(f"Unknown profile {value!r}; choose from {sorted(PROFILES)}") from exc
