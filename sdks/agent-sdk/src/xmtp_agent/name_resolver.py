"""Name resolution utilities."""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Final, Generic, TypeVar, cast
from urllib.parse import quote
from urllib.request import Request, urlopen

from xmtp.utils import is_hex_string

from xmtp_agent.errors import AgentError


class _MissingType:
    __slots__ = ()


_MISSING: Final = _MissingType()
T = TypeVar("T")


class _LimitedCache(Generic[T]):
    def __init__(self, limit: int = 1000) -> None:
        self._limit = limit
        self._data: OrderedDict[str, T] = OrderedDict()

    def get(self, key: str) -> T | _MissingType:
        if key not in self._data:
            return _MISSING
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: str, value: T) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self._limit:
            self._data.popitem(last=False)


def create_name_resolver(api_key: str | None = None) -> Callable[[str], Awaitable[str | None]]:
    """Create an async name resolver backed by web3.bio."""

    cache: _LimitedCache[str | None] = _LimitedCache(1000)

    async def resolve_name(name: str) -> str | None:
        if is_hex_string(name, length=40):
            return name

        cached = cache.get(name)
        if cached is not _MISSING:
            return cast(str | None, cached)

        def fetch() -> list[dict[str, object]]:
            endpoint = f"https://api.web3.bio/ns/{quote(name)}"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-API-KEY"] = f"Bearer {api_key}"
            request = Request(endpoint, headers=headers, method="GET")
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise AgentError(
                        f'Could not resolve address for name "{name}": '
                        f"{response.status} {response.reason}"
                    )
                data = response.read()
            return cast(list[dict[str, object]], json.loads(data.decode("utf-8")))

        results = await asyncio.to_thread(fetch)
        address_value = results[0].get("address") if results else None
        address = address_value if isinstance(address_value, str) else None
        cache.set(name, address)
        return address

    return resolve_name


__all__ = ["create_name_resolver"]
