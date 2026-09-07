"""A small, licensed-in-project UA catalog with parsing and filtering helpers.

The catalog intentionally ships a curated set rather than copying a third-party
database. Applications can provide their own dataset to UserAgentDatabase.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Iterable


BUILTIN_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (iPad; CPU OS 17_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
)


@dataclass(frozen=True, slots=True)
class ParsedUserAgent:
    raw: str
    browser: str
    version: str | None
    platform: str
    device: str


def parse(user_agent: str) -> ParsedUserAgent:
    browser, version = "unknown", None
    for name, pattern in (
        ("edge", r"Edg/([\d.]+)"),
        ("chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
        ("firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
        ("safari", r"Version/([\d.]+).*Safari/"),
    ):
        match = re.search(pattern, user_agent)
        if match:
            browser, version = name, match.group(1)
            break
    if "Windows" in user_agent:
        platform = "windows"
    elif "Mac OS X" in user_agent:
        platform = "macos"
    elif "Linux" in user_agent:
        platform = "linux"
    elif "Android" in user_agent:
        platform = "android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        platform = "ios"
    else:
        platform = "unknown"
    device = "mobile" if "Mobile" in user_agent or "iPhone" in user_agent else "desktop"
    return ParsedUserAgent(user_agent, browser, version, platform, device)


class UserAgentDatabase:
    def __init__(self, values: Iterable[str] = BUILTIN_USER_AGENTS) -> None:
        self._values = tuple(dict.fromkeys(values))
        if not self._values:
            raise ValueError("UserAgentDatabase requires at least one user-agent")

    def all(self) -> tuple[str, ...]:
        return self._values

    def random(self, *, seed: int | None = None) -> str:
        return random.Random(seed).choice(self._values) if seed is not None else random.choice(self._values)

    def filter(self, *, browser: str | None = None, platform: str | None = None, device: str | None = None) -> tuple[str, ...]:
        return tuple(
            value
            for value in self._values
            if (browser is None or parse(value).browser == browser.lower())
            and (platform is None or parse(value).platform == platform.lower())
            and (device is None or parse(value).device == device.lower())
        )

    def browser(self, name: str) -> str:
        values = self.filter(browser=name)
        if not values:
            raise LookupError(f"No user-agent found for browser {name!r}")
        return values[0]

    def chrome(self) -> str:
        return self.browser("chrome")

    def firefox(self) -> str:
        return self.browser("firefox")

    def edge(self) -> str:
        return self.browser("edge")

    def safari(self) -> str:
        return self.browser("safari")

    def mobile(self) -> str:
        values = self.filter(device="mobile")
        if not values:
            raise LookupError("No mobile user-agent found")
        return values[0]


ua = UserAgentDatabase()


def random() -> str:
    return ua.random()


def chrome() -> str:
    return ua.browser("chrome")


def firefox() -> str:
    return ua.browser("firefox")


def mobile() -> str:
    values = ua.filter(device="mobile")
    return values[0]
