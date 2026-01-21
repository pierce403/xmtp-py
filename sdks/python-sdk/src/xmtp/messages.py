"""Message models for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

ContentT = TypeVar("ContentT")


@dataclass(slots=True)
class DecodedMessage(Generic[ContentT]):
    """Decoded message representation."""

    id: bytes
    conversation_id: bytes
    sender_inbox_id: str
    sent_at: datetime
    content: ContentT
    content_type_id: str | None = None
