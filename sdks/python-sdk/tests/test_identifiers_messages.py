from datetime import datetime, timezone

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.messages import DecodedMessage


def test_identifier_dataclass() -> None:
    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
    assert identifier.kind == IdentifierKind.ETHEREUM
    assert identifier.value == '0xabc'


def test_decoded_message_dataclass() -> None:
    now = datetime.now(timezone.utc)
    message = DecodedMessage(
        id=b'1',
        conversation_id=b'2',
        sender_inbox_id='inbox',
        sent_at=now,
        content='hi',
        content_type_id='xmtp.org/text:1.0',
    )
    assert message.content == 'hi'
    assert message.sent_at == now
