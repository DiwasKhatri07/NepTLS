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
    is_chrome = browser in {"chrome", "edge"}
    platform_hint = {
        "windows": '"Windows"',
        "macos": '"macOS"',
        "linux": '"Linux"',
        "android": '"Android"',
        "ios": '"iOS"',
    }.get(platform, f'"{platform}"')
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if is_chrome:
        brand = "Microsoft Edge" if browser == "edge" else "Google Chrome"
        headers.update(
            {
                "Cache-Control": "max-age=0",
                "Sec-CH-UA": f'"Not A(Brand";v="99", "{brand}";v="{version.split(".")[0]}", "Chromium";v="{version.split(".")[0]}"',
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


CURL_CFFI_IMPERSONATE_MAP: dict[str, str] = {
    "chrome": "chrome131",
    "chrome-windows": "chrome131",
    "chrome-macos": "chrome131",
    "chrome-linux": "chrome131",
    "chrome-android": "chrome131",
    "chrome120": "chrome120",
    "chrome124": "chrome124",
    "chrome131": "chrome131",
    "chrome133": "chrome131",
    "firefox": "firefox133",
    "firefox133": "firefox133",
    "firefox120": "firefox120",
    "edge": "edge131",
    "edge131": "edge131",
    "safari": "safari17_0",
    "safari17": "safari17_0",
    "safari18": "safari17_0",
    "safari-ios": "safari_ios_17_0",
}


PROFILES = {
    "chrome": _profile("chrome", "chrome", "131.0", "windows", chrome()),
    "chrome-windows": _profile("chrome-windows", "chrome", "131.0", "windows", chrome()),
    "chrome-macos": _profile("chrome-macos", "chrome", "131.0", "macos", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "chrome-linux": _profile("chrome-linux", "chrome", "131.0", "linux", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "chrome-android": _profile("chrome-android", "chrome", "131.0", "android", mobile()),
    "chrome120": _profile("chrome120", "chrome", "120.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "chrome124": _profile("chrome124", "chrome", "124.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "chrome131": _profile("chrome131", "chrome", "131.0", "windows", chrome()),
    "chrome133": _profile("chrome133", "chrome", "133.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"),
    "firefox": _profile("firefox", "firefox", "133.0", "linux", firefox()),
    "firefox120": _profile("firefox120", "firefox", "120.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"),
    "firefox133": _profile("firefox133", "firefox", "133.0", "linux", firefox()),
    "edge": _profile("edge", "edge", "131.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"),
    "edge131": _profile("edge131", "edge", "131.0", "windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"),
    "safari": _profile("safari", "safari", "18.1", "macos", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"),
    "safari17": _profile("safari17", "safari", "17.6", "macos", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"),
    "safari18": _profile("safari18", "safari", "18.1", "macos", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"),
    "safari-ios": _profile("safari-ios", "safari", "18.1", "ios", mobile()),
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


def get_curl_cffi_impersonate(value: str | BrowserProfile | None) -> str | None:
    """Resolve an impersonate/profile name to a valid curl_cffi impersonate target string."""
    if value is None:
        return None
    if isinstance(value, BrowserProfile):
        name = value.name.lower()
    else:
        name = str(value).lower()
    return CURL_CFFI_IMPERSONATE_MAP.get(name, CURL_CFFI_IMPERSONATE_MAP.get(name.split("-")[0], name))
