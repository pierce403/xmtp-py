from datetime import datetime, timezone

from xmtp.conversation import Dm, Group
from xmtp.messages import DecodedMessage
from xmtp_agent.filters import (
    from_self,
    has_content,
    is_dm,
    is_group,
    is_group_update,
    is_markdown,
    is_reaction,
    is_read_receipt,
    is_remote_attachment,
    is_reply,
    is_text,
    is_transaction_reference,
    is_wallet_send_calls,
    uses_codec,
)
from xmtp_content_type_group_updated import ContentTypeGroupUpdated
from xmtp_content_type_markdown import ContentTypeMarkdown, MarkdownCodec
from xmtp_content_type_reaction import ContentTypeReaction
from xmtp_content_type_read_receipt import ContentTypeReadReceipt
from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment
from xmtp_content_type_reply import ContentTypeReply
from xmtp_content_type_text import ContentTypeText, TextCodec
from xmtp_content_type_transaction_reference import ContentTypeTransactionReference
from xmtp_content_type_wallet_send_calls import ContentTypeWalletSendCalls


def _message(content_type_id: str, content: object) -> DecodedMessage[object]:
    return DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content=content,
        content_type_id=content_type_id,
    )


def test_basic_filters() -> None:
    client = type('Client', (), {'inbox_id': 'sender'})()
    message = _message(str(ContentTypeText), 'hello')
    assert from_self(message, client) is True
    client_other = type('Client', (), {'inbox_id': 'other'})()
    assert from_self(message, client_other) is False
    assert has_content(message) is True
    assert is_text(message) is True
    assert is_markdown(_message(str(ContentTypeMarkdown), 'md')) is True
    assert is_reaction(_message(str(ContentTypeReaction), {})) is True
    assert is_reply(_message(str(ContentTypeReply), {})) is True
    assert is_remote_attachment(_message(str(ContentTypeRemoteAttachment), {})) is True
    assert is_read_receipt(_message(str(ContentTypeReadReceipt), {})) is True
    assert is_group_update(_message(str(ContentTypeGroupUpdated), {})) is True
    assert is_transaction_reference(_message(str(ContentTypeTransactionReference), {})) is True
    assert is_wallet_send_calls(_message(str(ContentTypeWalletSendCalls), {})) is True
    assert has_content(_message(str(ContentTypeText), None)) is False


def test_dm_group_filters() -> None:
    dm = Dm(object(), object())
    group = Group(object(), object())
    assert is_dm(dm) is True
    assert is_group(dm) is False
    assert is_dm(group) is False
    assert is_group(group) is True


def test_uses_codec() -> None:
    text_message = _message(str(ContentTypeText), 'hi')
    assert uses_codec(text_message, TextCodec) is True
    markdown_message = _message(str(ContentTypeMarkdown), 'md')
    assert uses_codec(markdown_message, MarkdownCodec) is True
