"""Name resolution utilities."""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from typing import Any, Awaitable, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from xmtp_agent.errors import AgentError
from xmtp.utils import is_hex_string


_MISSING = object()


class _LimitedCache:
    def __init__(self, limit: int = 1000) -> None:
        self._limit = limit
        self._data: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any:
        if key not in self._data:
            return _MISSING
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self._limit:
            self._data.popitem(last=False)


def create_name_resolver(api_key: str | None = None) -> Callable[[str], Awaitable[str | None]]:
    """Create an async name resolver backed by web3.bio."""

    cache = _LimitedCache(1000)

    async def resolve_name(name: str) -> str | None:
        if is_hex_string(name, length=40):
            return name

        cached = cache.get(name)
        if cached is not _MISSING:
            return cached

        def fetch() -> list[dict[str, Any]]:
            endpoint = f'https://api.web3.bio/ns/{quote(name)}'
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['X-API-KEY'] = f'Bearer {api_key}'
            request = Request(endpoint, headers=headers, method='GET')
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise AgentError(
                        f'Could not resolve address for name "{name}": '
                        f'{response.status} {response.reason}'
                    )
                data = response.read()
            return json.loads(data.decode('utf-8'))

        results = await asyncio.to_thread(fetch)
        address = results[0].get('address') if results else None
        cache.set(name, address)
        return address

    return resolve_name


__all__ = ['create_name_resolver']
