"""Reusable rotation pools."""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class PoolStats:
    selections: int = 0
    failures: int = 0


class Pool(Generic[T]):
    def __init__(self, values: Iterable[T], *, strategy: str = "round_robin", seed: int | None = None) -> None:
        self._values = list(values)
        if not self._values:
            raise ValueError("Pool requires at least one value")
        if strategy not in {"round_robin", "random"}:
            raise ValueError("strategy must be 'round_robin' or 'random'")
        self.strategy = strategy
        self._index = 0
        self._random = random.Random(seed)
        self.stats = PoolStats()

    def next(self) -> T:
        if self.strategy == "random":
            value = self._random.choice(self._values)
        else:
            value = self._values[self._index % len(self._values)]
            self._index += 1
        self.stats.selections += 1
        return value

    def record_failure(self) -> None:
        self.stats.failures += 1

    def add(self, value: T) -> None:
        self._values.append(value)

    def remove(self, value: T) -> None:
        self._values.remove(value)

    def __len__(self) -> int:
        return len(self._values)


ProfilePool = Pool
ClientPool = Pool
TLSProfilePool = Pool
BrowserProfilePool = Pool
UserAgentPool = Pool
ProxyPool = Pool
