import asyncio

import pytest

from xmtp_agent.errors import AgentStreamingError
from xmtp_agent.middleware import backoff_reconnect


@pytest.mark.asyncio
async def test_backoff_reconnect_handles_streaming_error(monkeypatch) -> None:
    calls = {'sleep': None, 'next': 'unset'}

    async def fake_sleep(delay: float) -> None:
        calls['sleep'] = delay

    async def next_handler(exc=None) -> None:
        calls['next'] = exc

    monkeypatch.setattr(asyncio, 'sleep', fake_sleep)

    middleware = backoff_reconnect(initial_delay=0.0, max_delay=1.0)
    await middleware(AgentStreamingError('boom'), object(), next_handler)

    assert calls['sleep'] == 0.0
    assert calls['next'] is None


@pytest.mark.asyncio
async def test_backoff_reconnect_passthrough() -> None:
    calls = {'next': 'unset'}

    async def next_handler(exc=None) -> None:
        calls['next'] = exc

    middleware = backoff_reconnect(initial_delay=0.0, max_delay=1.0)
    error = RuntimeError('boom')
    await middleware(error, object(), next_handler)

    assert calls['next'] is error


@pytest.mark.asyncio
async def test_backoff_reconnect_resets_after(monkeypatch) -> None:
    times = iter([0.0, 10.0, 20.0])

    def fake_monotonic() -> float:
        return next(times)

    async def fake_sleep(delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, 'sleep', fake_sleep)
    monkeypatch.setattr('xmtp_agent.middleware.time.monotonic', fake_monotonic)

    middleware = backoff_reconnect(initial_delay=1.0, max_delay=4.0, multiplier=2.0, reset_after=5.0)

    async def next_handler(exc=None) -> None:
        return None

    await middleware(AgentStreamingError('boom'), object(), next_handler)
    await middleware(AgentStreamingError('boom'), object(), next_handler)
