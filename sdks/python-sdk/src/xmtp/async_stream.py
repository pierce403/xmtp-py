"""Async stream helper."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")

_END = object()


class AsyncStream(AsyncIterator[T], Generic[T]):
    """Async stream backed by an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue[object],
        closer: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._queue = queue
        self._closer = closer

    def __aiter__(self) -> AsyncStream[T]:
        return self

    async def __anext__(self) -> T:
        item = await self._queue.get()
        if item is _END:
            raise StopAsyncIteration
        return item  # type: ignore[return-value]

    async def close(self) -> None:
        """Close the underlying stream if possible."""

        if self._closer is None:
            return
        await self._closer()

    def _end(self) -> None:
        """Signal end-of-stream to consumers."""

        self._queue.put_nowait(_END)
