import asyncio
import json

import pytest

from xmtp_agent.name_resolver import _LimitedCache, create_name_resolver


class _Response:
    def __init__(self, status: int, data: bytes) -> None:
        self.status = status
        self.reason = 'OK' if status < 400 else 'Bad'
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_name_resolver_returns_address_without_lookup(monkeypatch) -> None:
    resolver = create_name_resolver()
    address = '0x' + '1' * 40
    assert await resolver(address) == address


@pytest.mark.asyncio
async def test_name_resolver_caches(monkeypatch) -> None:
    payload = json.dumps([{'address': '0x' + '2' * 40}]).encode('utf-8')

    calls = {'count': 0}

    def fake_urlopen(request, timeout=10):
        calls['count'] += 1
        return _Response(200, payload)

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.name_resolver.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    resolver = create_name_resolver()
    assert await resolver('test.eth') == '0x' + '2' * 40
    assert await resolver('test.eth') == '0x' + '2' * 40
    assert calls['count'] == 1


@pytest.mark.asyncio
async def test_name_resolver_http_error(monkeypatch) -> None:
    def fake_urlopen(request, timeout=10):
        return _Response(500, b'')

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.name_resolver.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    resolver = create_name_resolver()
    with pytest.raises(Exception, match='Could not resolve address'):
        await resolver('test.eth')


def test_limited_cache_eviction() -> None:
    cache = _LimitedCache(limit=1)
    cache.set('a', 1)
    cache.set('b', 2)
    assert cache.get('a') is not 1
    assert cache.get('b') == 2


@pytest.mark.asyncio
async def test_name_resolver_api_key(monkeypatch) -> None:
    payload = json.dumps([{'address': '0x' + '3' * 40}]).encode('utf-8')

    def fake_urlopen(request, timeout=10):
        header = request.headers.get('X-API-KEY') or request.headers.get('X-api-key')
        assert header == 'Bearer token'
        return _Response(200, payload)

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.name_resolver.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    resolver = create_name_resolver(api_key='token')
    assert await resolver('test.eth') == '0x' + '3' * 40


@pytest.mark.asyncio
async def test_name_resolver_empty_results(monkeypatch) -> None:
    payload = json.dumps([]).encode('utf-8')

    def fake_urlopen(request, timeout=10):
        return _Response(200, payload)

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.name_resolver.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    resolver = create_name_resolver()
    assert await resolver('test.eth') is None
