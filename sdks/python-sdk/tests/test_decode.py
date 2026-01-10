from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from xmtp.client import Client
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp_content_type_primitives import ContentTypeId, EncodedContent
from xmtp_content_type_reply import Reply
from xmtp_content_type_remote_attachment import Attachment, RemoteAttachment
from xmtp_content_type_text import ContentTypeText, TextCodec
from xmtp_content_type_transaction_reference import TransactionMetadata, TransactionReference
from xmtp_content_type_wallet_send_calls import WalletCall, WalletCallMetadata, WalletSendCalls


class _DecodedContent:
    def __init__(self, kind: str, payload: Any) -> None:
        self._kind = kind
        self._payload = payload

    def __getitem__(self, index: int) -> Any:
        if index != 0:
            raise IndexError
        return self._payload

    def is_TEXT(self) -> bool:
        return self._kind == 'TEXT'

    def is_MARKDOWN(self) -> bool:
        return self._kind == 'MARKDOWN'

    def is_REACTION(self) -> bool:
        return self._kind == 'REACTION'

    def is_REPLY(self) -> bool:
        return self._kind == 'REPLY'

    def is_REMOTE_ATTACHMENT(self) -> bool:
        return self._kind == 'REMOTE_ATTACHMENT'

    def is_READ_RECEIPT(self) -> bool:
        return self._kind == 'READ_RECEIPT'

    def is_TRANSACTION_REFERENCE(self) -> bool:
        return self._kind == 'TRANSACTION_REFERENCE'

    def is_WALLET_SEND_CALLS(self) -> bool:
        return self._kind == 'WALLET_SEND_CALLS'

    def is_GROUP_UPDATED(self) -> bool:
        return self._kind == 'GROUP_UPDATED'

    def is_ATTACHMENT(self) -> bool:
        return self._kind == 'ATTACHMENT'

    def is_ACTIONS(self) -> bool:
        return self._kind == 'ACTIONS'

    def is_INTENT(self) -> bool:
        return self._kind == 'INTENT'

    def is_LEAVE_REQUEST(self) -> bool:
        return self._kind == 'LEAVE_REQUEST'

    def is_CUSTOM(self) -> bool:
        return self._kind == 'CUSTOM'


@dataclass
class _FakeReaction:
    reference: str
    reference_inbox_id: str
    action: Any
    content: str
    schema: Any


@dataclass
class _FakeReplyPayload:
    reference: str
    reference_inbox_id: str | None
    content: Any


@dataclass
class _FakeRemoteAttachment:
    url: str
    content_digest: str
    secret: bytes
    salt: bytes
    nonce: bytes
    scheme: str
    content_length: int
    filename: str | None


@dataclass
class _FakeAttachment:
    filename: str | None
    mime_type: str
    content: bytes


@dataclass
class _FakeTransactionMetadata:
    transaction_type: str
    currency: str
    amount: float
    decimals: int
    from_address: str
    to_address: str


@dataclass
class _FakeTransactionReference:
    namespace: str
    network_id: str
    reference: str
    metadata: _FakeTransactionMetadata | None


@dataclass
class _FakeWalletCallMetadata:
    description: str
    transaction_type: str
    extra: dict[str, str]


@dataclass
class _FakeWalletCall:
    to: str | None
    data: str | None
    value: str | None
    gas: str | None
    metadata: _FakeWalletCallMetadata | None


@dataclass
class _FakeWalletSendCalls:
    version: str
    chain_id: str
    _from: str
    calls: list[_FakeWalletCall]
    capabilities: dict[str, str] | None


class _FakeEncoded:
    def __init__(self, type_id: Any) -> None:
        self.type_id = type_id
        self.parameters = {'encoding': 'UTF-8'}
        self.fallback = None
        self.compression = None
        self.content = b'data'


class _Codec:
    def __init__(self, content_type: ContentTypeId) -> None:
        self._content_type = content_type

    @property
    def content_type(self) -> ContentTypeId:
        return self._content_type

    def encode(self, content: Any, registry: Any) -> EncodedContent:
        return EncodedContent(type_id=self._content_type, parameters={}, content=b'decoded')

    def decode(self, content: EncodedContent, registry: Any) -> Any:
        return 'decoded-content'

    def fallback(self, content: Any) -> str | None:
        return None

    def should_push(self, content: Any) -> bool:
        return True


@pytest.mark.asyncio
async def test_decode_message_branches(fake_bindings) -> None:
    client = Client()

    reaction = _FakeReaction(
        reference='ref',
        reference_inbox_id='inbox',
        action=fake_bindings.FfiReactionAction.ADDED,
        content='smile',
        schema=fake_bindings.FfiReactionSchema.UNICODE,
    )
    reply_inner = _FakeEncoded(
        fake_bindings.FfiContentTypeId('xmtp.org', 'text', 1, 0)
    )
    reply_payload = _FakeReplyPayload(reference='ref', reference_inbox_id=None, content=reply_inner)
    remote_attachment = _FakeRemoteAttachment(
        url='https://example',
        content_digest='digest',
        secret=b'secret',
        salt=b'salt',
        nonce=b'nonce',
        scheme='https',
        content_length=10,
        filename='file',
    )
    attachment = _FakeAttachment(filename='file', mime_type='text/plain', content=b'data')
    tx_meta = _FakeTransactionMetadata(
        transaction_type='transfer',
        currency='ETH',
        amount=1.0,
        decimals=18,
        from_address='0xabc',
        to_address='0xdef',
    )
    tx_payload = _FakeTransactionReference(
        namespace='eip155',
        network_id='1',
        reference='0x123',
        metadata=tx_meta,
    )
    wallet_payload = _FakeWalletSendCalls(
        version='1.0',
        chain_id='1',
        _from='0xabc',
        calls=[
            _FakeWalletCall(
                to='0xdef',
                data=None,
                value='0x1',
                gas=None,
                metadata=_FakeWalletCallMetadata(
                    description='desc',
                    transaction_type='transfer',
                    extra={'foo': 'bar'},
                ),
            )
        ],
        capabilities={'cap': '1'},
    )

    client.register_codec(_Codec(ContentTypeText))

    assert client._decode_ffi_content(_DecodedContent('TEXT', type('T', (), {'content': 'hi'})())) == 'hi'
    assert client._decode_ffi_content(_DecodedContent('MARKDOWN', type('M', (), {'content': '*hi*'})())) == '*hi*'

    decoded_reaction = client._decode_ffi_content(_DecodedContent('REACTION', reaction))
    assert decoded_reaction.content == 'smile'

    decoded_reply = client._decode_ffi_content(_DecodedContent('REPLY', reply_payload))
    assert isinstance(decoded_reply, Reply)
    assert decoded_reply.content == 'decoded-content'

    decoded_remote = client._decode_ffi_content(_DecodedContent('REMOTE_ATTACHMENT', remote_attachment))
    assert isinstance(decoded_remote, RemoteAttachment)

    assert client._decode_ffi_content(_DecodedContent('READ_RECEIPT', {})) == {}

    decoded_tx = client._decode_ffi_content(_DecodedContent('TRANSACTION_REFERENCE', tx_payload))
    assert isinstance(decoded_tx, TransactionReference)
    assert decoded_tx.metadata is not None

    decoded_wallet = client._decode_ffi_content(_DecodedContent('WALLET_SEND_CALLS', wallet_payload))
    assert isinstance(decoded_wallet, WalletSendCalls)
    assert decoded_wallet.calls[0].metadata is not None

    assert client._decode_ffi_content(_DecodedContent('GROUP_UPDATED', 'payload')) == 'payload'

    decoded_attachment = client._decode_ffi_content(_DecodedContent('ATTACHMENT', attachment))
    assert isinstance(decoded_attachment, Attachment)

    assert client._decode_ffi_content(_DecodedContent('ACTIONS', 'actions')) == 'actions'
    assert client._decode_ffi_content(_DecodedContent('INTENT', 'intent')) == 'intent'
    assert client._decode_ffi_content(_DecodedContent('LEAVE_REQUEST', 'leave')) == 'leave'

    bad_custom = fake_bindings.FfiEncodedContent(
        type_id=None,
        parameters={},
        fallback=None,
        compression=None,
        content=b'data',
    )
    assert client._decode_ffi_content(_DecodedContent('CUSTOM', bad_custom)) is bad_custom

    missing_codec = fake_bindings.FfiEncodedContent(
        type_id=fake_bindings.FfiContentTypeId('xmtp.org', 'missing', 1, 0),
        parameters={},
        fallback=None,
        compression=None,
        content=b'data',
    )
    assert client._decode_ffi_content(_DecodedContent('CUSTOM', missing_codec)) is missing_codec

    custom_encoded = fake_bindings.FfiEncodedContent(
        type_id=fake_bindings.FfiContentTypeId('xmtp.org', 'text', 1, 0),
        parameters={'encoding': 'UTF-8'},
        fallback=None,
        compression=None,
        content=b'data',
    )
    decoded_custom = client._decode_ffi_content(_DecodedContent('CUSTOM', custom_encoded))
    assert decoded_custom == 'decoded-content'

    unknown = _DecodedContent('UNKNOWN', 'value')
    assert client._decode_ffi_content(unknown) is unknown


@pytest.mark.asyncio
async def test_decode_message(fake_bindings) -> None:
    client = Client()

    class _Enriched:
        def __init__(self) -> None:
            self._content = _DecodedContent('TEXT', type('T', (), {'content': 'hi'})())

        def content(self) -> Any:
            return self._content

        def sent_at_ns(self) -> int:
            return 1_000_000_000

        def content_type_id(self) -> Any:
            return fake_bindings.FfiContentTypeId('xmtp.org', 'text', 1, 0)

        def id(self) -> bytes:
            return b'id'

        def conversation_id(self) -> bytes:
            return b'cid'

        def sender_inbox_id(self) -> str:
            return 'inbox'

    class _FfiClient:
        def enriched_message(self, message_id: bytes) -> _Enriched:
            return _Enriched()

    class _Message:
        def __init__(self) -> None:
            self.id = b'message'

    client._client = _FfiClient()
    decoded = client._decode_message(_Message())
    assert decoded.content == 'hi'
    assert decoded.sent_at == datetime.fromtimestamp(1, tz=timezone.utc)


def test_decode_message_requires_client() -> None:
    client = Client()

    class _Message:
        def __init__(self) -> None:
            self.id = b'message'

    with pytest.raises(Exception, match='Client not initialized'):
        client._decode_message(_Message())
