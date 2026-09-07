"""Generic proof-of-work primitives for protocol research."""

from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .exceptions import PowError


@dataclass(frozen=True, slots=True)
class Challenge:
    payload: bytes | str
    difficulty: int = 4
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.difficulty < 1:
            raise PowError("difficulty must be at least 1")
        try:
            hashlib.new(self.algorithm)
        except ValueError as exc:
            raise PowError(f"unsupported hash algorithm: {self.algorithm}") from exc

    @property
    def payload_bytes(self) -> bytes:
        return self.payload.encode() if isinstance(self.payload, str) else self.payload


@dataclass(frozen=True, slots=True)
class Result:
    nonce: int
    digest: str
    attempts: int
    duration: float


def digest(challenge: Challenge, nonce: int) -> str:
    return hashlib.new(challenge.algorithm, challenge.payload_bytes + str(nonce).encode()).hexdigest()


def verify(challenge: Challenge, nonce: int) -> bool:
    return digest(challenge, nonce).startswith("0" * challenge.difficulty)


def solve(challenge: Challenge, *, start: int = 0, max_attempts: int = 10_000_000) -> Result:
    started = time.perf_counter()
    prefix = "0" * challenge.difficulty
    for attempts, nonce in enumerate(range(start, start + max_attempts), start=1):
        value = digest(challenge, nonce)
        if value.startswith(prefix):
            return Result(nonce, value, attempts, time.perf_counter() - started)
    raise PowError(f"no solution found in {max_attempts} attempts")


def solve_parallel(
    challenge: Challenge,
    *,
    workers: int = 4,
    start: int = 0,
    max_attempts: int = 10_000_000,
) -> Result:
    """Search independent nonce ranges concurrently.

    This is a generic benchmark/research primitive. It is not tied to any
    CAPTCHA, authentication, payment, or anti-abuse mechanism.
    """
    if workers <= 0:
        raise ValueError("workers must be greater than zero")
    started = time.perf_counter()
    stop = __import__("threading").Event()
    prefix = "0" * challenge.difficulty
    per_worker = max(1, (max_attempts + workers - 1) // workers)

    def search(worker: int) -> tuple[int, str, int] | None:
        first = start + worker * per_worker
        last = min(start + max_attempts, first + per_worker)
        attempts = 0
        for nonce in range(first, last):
            if stop.is_set():
                return None
            attempts += 1
            value = digest(challenge, nonce)
            if value.startswith(prefix):
                stop.set()
                return nonce, value, attempts
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(search, worker) for worker in range(workers)]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                nonce, value, attempts = result
                return Result(nonce, value, attempts, time.perf_counter() - started)
    raise PowError(f"no solution found in {max_attempts} attempts")


def benchmark(challenge: Challenge, *, attempts: int = 10_000) -> dict[str, float | int | str]:
    """Measure digest throughput without searching for a solution."""
    if attempts <= 0:
        raise ValueError("attempts must be greater than zero")
    started = time.perf_counter()
    for nonce in range(attempts):
        digest(challenge, nonce)
    duration = time.perf_counter() - started
    return {
        "algorithm": challenge.algorithm,
        "attempts": attempts,
        "duration": duration,
        "attempts_per_second": attempts / duration if duration else float("inf"),
    }
