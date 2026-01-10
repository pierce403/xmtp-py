"""Async stream helper."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Generic, TypeVar

T = TypeVar('T')


class AsyncStream(AsyncIterator[T], Generic[T]):
    """Wrapper for async iterators returned by XMTP stream APIs."""

    def __init__(self, iterator: AsyncIterator[T]) -> None:
        self._iterator = iterator

    def __aiter__(self) -> AsyncStream[T]:
        return self

    async def __anext__(self) -> T:
        return await self._iterator.__anext__()
