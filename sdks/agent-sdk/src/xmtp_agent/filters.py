"""Message filter helpers."""

from __future__ import annotations

from typing import Any, TypeVar

from xmtp import Client, Conversation, DecodedMessage, Dm, Group
from xmtp_content_type_group_updated import ContentTypeGroupUpdated
from xmtp_content_type_markdown import ContentTypeMarkdown
from xmtp_content_type_primitives import ContentCodec
from xmtp_content_type_reaction import ContentTypeReaction
from xmtp_content_type_read_receipt import ContentTypeReadReceipt
from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment
from xmtp_content_type_reply import ContentTypeReply
from xmtp_content_type_text import ContentTypeText
from xmtp_content_type_transaction_reference import ContentTypeTransactionReference
from xmtp_content_type_wallet_send_calls import ContentTypeWalletSendCalls

ContentT = TypeVar("ContentT")


def from_self(message: DecodedMessage[Any], client: Client) -> bool:
    return message.sender_inbox_id == client.inbox_id


def has_content(message: DecodedMessage[Any]) -> bool:
    return message.content is not None


def is_dm(conversation: Conversation) -> bool:
    return isinstance(conversation, Dm)


def is_group(conversation: Conversation) -> bool:
    return isinstance(conversation, Group)


def is_group_update(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeGroupUpdated)


def is_markdown(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeMarkdown)


def is_reaction(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeReaction)


def is_read_receipt(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeReadReceipt)


def is_remote_attachment(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeRemoteAttachment)


def is_reply(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeReply)


def is_text(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeText)


def is_transaction_reference(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeTransactionReference)


def is_wallet_send_calls(message: DecodedMessage[Any]) -> bool:
    return message.content_type_id == str(ContentTypeWalletSendCalls)


def uses_codec(message: DecodedMessage[Any], codec_class: type[ContentCodec[Any]]) -> bool:
    return message.content_type_id == str(codec_class().content_type)


class _Filter:
    from_self = staticmethod(from_self)
    has_content = staticmethod(has_content)
    is_dm = staticmethod(is_dm)
    is_group = staticmethod(is_group)
    is_group_update = staticmethod(is_group_update)
    is_markdown = staticmethod(is_markdown)
    is_reaction = staticmethod(is_reaction)
    is_read_receipt = staticmethod(is_read_receipt)
    is_remote_attachment = staticmethod(is_remote_attachment)
    is_reply = staticmethod(is_reply)
    is_text = staticmethod(is_text)
    is_transaction_reference = staticmethod(is_transaction_reference)
    is_wallet_send_calls = staticmethod(is_wallet_send_calls)
    uses_codec = staticmethod(uses_codec)


filter = _Filter()
f = filter

__all__ = [
    "filter",
    "f",
    "from_self",
    "has_content",
    "is_dm",
    "is_group",
    "is_group_update",
    "is_markdown",
    "is_reaction",
    "is_read_receipt",
    "is_remote_attachment",
    "is_reply",
    "is_text",
    "is_transaction_reference",
    "is_wallet_send_calls",
    "uses_codec",
]
