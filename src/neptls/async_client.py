"""Async API backed by the same tested synchronous transport."""

from __future__ import annotations

import asyncio
from typing import Any

from .client import Client
from .models import Response


class AsyncClient:
    """An asyncio-friendly client with a persistent cookie/profile session."""

    def __init__(self, **kwargs: Any) -> None:
        self._client = Client(**kwargs)

    async def request(self, method: str, url: str, **kwargs: Any) -> Response:
        return await asyncio.to_thread(self._client.request, method, url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Response:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Response:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> Response:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> Response:
        return await self.request("OPTIONS", url, **kwargs)

    def fingerprint(self):
        return self._client.fingerprint()

    @property
    def transport(self) -> str:
        return self._client.transport

    @property
    def protocol(self) -> str | None:
        return self._client.protocol

    @property
    def native_transport_available(self) -> bool:
        return self._client.native_transport_available

    async def close(self) -> None:
        await asyncio.to_thread(self._client.close)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
