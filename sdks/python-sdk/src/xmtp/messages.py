"""Message models for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

ContentT = TypeVar('ContentT')


@dataclass(slots=True)
class DecodedMessage(Generic[ContentT]):
    """Decoded message representation.

    Attributes:
        id: Message identifier.
        conversation_id: Conversation identifier.
        sender_address: Wallet address of the sender.
        sent_at: Timestamp when the message was sent.
        content: Decoded message content.
    """

    id: str
    conversation_id: str
    sender_address: str
    sent_at: datetime
    content: ContentT
