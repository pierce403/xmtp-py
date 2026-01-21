"""Testing utilities for agent development."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from xmtp.async_stream import AsyncStream
from xmtp.messages import DecodedMessage
from xmtp_content_type_text import ContentTypeText

ContentT = TypeVar("ContentT")


@dataclass(slots=True)
class _MessageOverrides(Generic[ContentT]):
    id: bytes | None = None
    conversation_id: bytes | None = None
    sender_inbox_id: str | None = None
    sent_at: datetime | None = None
    content_type_id: str | None = None
    content: ContentT | None = None


def create_mock_message(content: ContentT, **overrides: object) -> DecodedMessage[ContentT]:
    """Create a decoded message with sensible defaults for tests."""

    opts = _MessageOverrides[ContentT](content=content, **overrides)  # type: ignore[arg-type]
    return DecodedMessage(
        id=opts.id or b"mock-message-id",
        conversation_id=opts.conversation_id or b"test-conversation-id",
        sender_inbox_id=opts.sender_inbox_id or "sender-inbox-id",
        sent_at=opts.sent_at or datetime.now(tz=timezone.utc),
        content=content,
        content_type_id=opts.content_type_id or str(ContentTypeText),
    )


class MockAsyncStream(AsyncStream[ContentT], Generic[ContentT]):
    """Async stream helper with push/end for tests."""

    def __init__(self, values: Iterable[ContentT] | None = None) -> None:
        queue: asyncio.Queue[object] = asyncio.Queue()
        super().__init__(queue)
        if values is not None:
            for value in values:
                queue.put_nowait(value)

    def push(self, value: ContentT) -> None:
        self._queue.put_nowait(value)

    def end(self) -> None:
        self._end()

    async def close(self) -> None:
        self.end()


def serialize_message(message: DecodedMessage[Any]) -> dict[str, Any]:
    """Serialize a decoded message to a JSON-friendly dict."""

    return {
        "id": message.id.hex(),
        "conversation_id": message.conversation_id.hex(),
        "sender_inbox_id": message.sender_inbox_id,
        "sent_at": message.sent_at.isoformat(),
        "content": message.content,
        "content_type_id": message.content_type_id,
    }


def deserialize_message(payload: dict[str, Any]) -> DecodedMessage[Any]:
    """Deserialize a decoded message from a JSON-friendly dict."""

    return DecodedMessage(
        id=bytes.fromhex(payload["id"]),
        conversation_id=bytes.fromhex(payload["conversation_id"]),
        sender_inbox_id=payload["sender_inbox_id"],
        sent_at=datetime.fromisoformat(payload["sent_at"]),
        content=payload["content"],
        content_type_id=payload.get("content_type_id"),
    )


async def record_messages(
    stream: AsyncStream[DecodedMessage[Any]],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Record decoded messages from a stream."""

    recorded: list[dict[str, Any]] = []
    async for message in stream:
        recorded.append(serialize_message(message))
        if limit is not None and len(recorded) >= limit:
            break
    return recorded


def replay_messages(records: Iterable[dict[str, Any]]) -> MockAsyncStream[DecodedMessage[Any]]:
    """Replay recorded messages as an async stream."""

    messages = [deserialize_message(record) for record in records]
    stream: MockAsyncStream[DecodedMessage[Any]] = MockAsyncStream(messages)
    stream.end()
    return stream


async def flush_asyncio() -> None:
    """Flush the asyncio event loop for tests."""

    await asyncio.sleep(0)


__all__ = [
    "MockAsyncStream",
    "create_mock_message",
    "deserialize_message",
    "flush_asyncio",
    "record_messages",
    "replay_messages",
    "serialize_message",
]
