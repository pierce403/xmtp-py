import asyncio

import pytest

from xmtp.async_stream import AsyncStream


@pytest.mark.asyncio
async def test_async_stream_iterates_and_ends() -> None:
    queue: asyncio.Queue[object] = asyncio.Queue()
    stream = AsyncStream(queue)
    queue.put_nowait('one')
    stream._end()

    items = []
    async for item in stream:
        items.append(item)

    assert items == ['one']


@pytest.mark.asyncio
async def test_async_stream_close_calls_closer() -> None:
    queue: asyncio.Queue[object] = asyncio.Queue()
    closed = False

    async def closer() -> None:
        nonlocal closed
        closed = True

    stream = AsyncStream(queue, closer=closer)
    await stream.close()
    assert closed is True


@pytest.mark.asyncio
async def test_async_stream_close_without_closer() -> None:
    queue: asyncio.Queue[object] = asyncio.Queue()
    stream = AsyncStream(queue)
    await stream.close()
