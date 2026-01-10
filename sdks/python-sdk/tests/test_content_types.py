import json

import pytest

pytest.importorskip('xmtp_bindings')

from xmtp_content_type_group_updated import ContentTypeGroupUpdated, GroupUpdatedCodec
from xmtp_content_type_markdown import ContentTypeMarkdown, Encoding as MarkdownEncoding, MarkdownCodec
from xmtp_content_type_primitives import (
    ContentTypeId,
    EncodedContent,
    content_type_from_string,
    content_type_to_string,
    content_types_are_equal,
)
from xmtp_content_type_reaction import (
    ContentTypeReaction,
    Reaction,
    ReactionAction,
    ReactionCodec,
    ReactionSchema,
)
from xmtp_content_type_read_receipt import ContentTypeReadReceipt, ReadReceiptCodec
from xmtp_content_type_remote_attachment import (
    Attachment,
    AttachmentCodec,
    ContentTypeAttachment,
    ContentTypeRemoteAttachment,
    RemoteAttachment,
    RemoteAttachmentCodec,
)
from xmtp_content_type_reply import ContentTypeReply, Reply, ReplyCodec, _content_type_from_ffi
from xmtp_content_type_text import ContentTypeText, Encoding as TextEncoding, TextCodec
from xmtp_content_type_transaction_reference import (
    ContentTypeTransactionReference,
    TransactionMetadata,
    TransactionReference,
    TransactionReferenceCodec,
)
from xmtp_content_type_wallet_send_calls import (
    ContentTypeWalletSendCalls,
    WalletCall,
    WalletCallMetadata,
    WalletSendCalls,
    WalletSendCallsCodec,
)


class _Registry:
    def __init__(self, codecs):
        self._codecs = {str(codec.content_type): codec for codec in codecs}

    def codec_for(self, content_type):
        return self._codecs.get(str(content_type))


def test_text_codec_encode_decode() -> None:
    codec = TextCodec()
    encoded = codec.encode('Hello')
    assert encoded.type_id == ContentTypeText
    assert encoded.parameters['encoding'] == TextEncoding.UTF8.value
    assert codec.decode(encoded) == 'Hello'
    assert codec.fallback('Hello') is None
    assert codec.should_push('Hello') is True


def test_text_codec_unknown_encoding() -> None:
    codec = TextCodec()
    encoded = EncodedContent(
        type_id=ContentTypeText,
        parameters={'encoding': 'UTF-16'},
        content=b'',
    )
    with pytest.raises(ValueError, match='unrecognized encoding UTF-16'):
        codec.decode(encoded)


def test_text_codec_invalid_payload_type() -> None:
    codec = TextCodec()
    encoded = EncodedContent(
        type_id=ContentTypeText,
        parameters={'encoding': TextEncoding.UTF8.value},
        content=object(),
    )
    with pytest.raises(TypeError):
        codec.decode(encoded)


def test_markdown_codec_encode_decode() -> None:
    codec = MarkdownCodec()
    encoded = codec.encode('*hi*')
    assert encoded.type_id == ContentTypeMarkdown
    assert encoded.parameters['encoding'] == MarkdownEncoding.UTF8.value
    assert codec.decode(encoded) == '*hi*'
    assert codec.fallback('*hi*') is None
    assert codec.should_push('*hi*') is True


def test_markdown_codec_unknown_encoding() -> None:
    codec = MarkdownCodec()
    encoded = EncodedContent(
        type_id=ContentTypeMarkdown,
        parameters={'encoding': 'UTF-16'},
        content=b'',
    )
    with pytest.raises(ValueError, match='unrecognized encoding UTF-16'):
        codec.decode(encoded)


def test_markdown_codec_invalid_payload_type() -> None:
    codec = MarkdownCodec()
    encoded = EncodedContent(
        type_id=ContentTypeMarkdown,
        parameters={'encoding': MarkdownEncoding.UTF8.value},
        content=123,
    )
    with pytest.raises(TypeError):
        codec.decode(encoded)


def test_content_type_from_string_errors() -> None:
    with pytest.raises(ValueError, match='Invalid content type string: "foo/bar"'):
        content_type_from_string('foo/bar')
    with pytest.raises(ValueError, match='Invalid content type string: "foo:1.0"'):
        content_type_from_string('foo:1.0')
    with pytest.raises(ValueError, match='Invalid content type string: "foo/bar:a.b"'):
        content_type_from_string('foo/bar:a.b')
    with pytest.raises(ValueError, match='Invalid content type string: ""'):
        content_type_from_string('')


def test_content_type_from_string_success() -> None:
    content_type = content_type_from_string('xmtp.org/text:1.0')
    assert content_type.authority_id == 'xmtp.org'
    assert content_type.type_id == 'text'
    assert content_type.version_major == 1
    assert content_type.version_minor == 0


def test_content_type_helpers() -> None:
    left = ContentTypeId(authority_id='xmtp.org', type_id='text', version_major=1, version_minor=0)
    right = ContentTypeId(authority_id='xmtp.org', type_id='text', version_major=1, version_minor=0)
    other = ContentTypeId(authority_id='xmtp.org', type_id='markdown', version_major=1, version_minor=0)
    assert content_types_are_equal(left, right) is True
    assert content_types_are_equal(left, other) is False
    assert content_type_to_string(left) == 'xmtp.org/text:1.0'


def test_reaction_codec_canonical_and_legacy() -> None:
    codec = ReactionCodec()
    canonical_payload = {
        'action': 'added',
        'content': 'smile',
        'reference': 'abc123',
        'schema': 'shortcode',
    }
    canonical = EncodedContent(
        type_id=ContentTypeReaction,
        parameters={
            'action': 'added',
            'reference': 'abc123',
            'schema': 'shortcode',
            'encoding': 'UTF-8',
        },
        content=json.dumps(canonical_payload).encode('utf-8'),
    )
    legacy = EncodedContent(
        type_id=ContentTypeReaction,
        parameters={
            'action': 'added',
            'reference': 'abc123',
            'schema': 'shortcode',
            'encoding': 'UTF-8',
        },
        content=b'smile',
    )

    decoded_canonical = codec.decode(canonical)
    decoded_legacy = codec.decode(legacy)

    assert decoded_canonical.action == ReactionAction.ADDED
    assert decoded_legacy.action == ReactionAction.ADDED
    assert decoded_canonical.content == 'smile'
    assert decoded_legacy.content == 'smile'
    assert decoded_canonical.reference == 'abc123'
    assert decoded_legacy.reference == 'abc123'
    assert decoded_canonical.schema == ReactionSchema.SHORTCODE
    assert decoded_legacy.schema == ReactionSchema.SHORTCODE


def test_reaction_codec_ffi_fallback(monkeypatch) -> None:
    codec = ReactionCodec()
    from xmtp_bindings import xmtpv3

    payload = xmtpv3.FfiReactionPayload(
        reference='ref',
        reference_inbox_id='inbox',
        action=xmtpv3.FfiReactionAction.ADDED,
        content='smile',
        schema=xmtpv3.FfiReactionSchema.UNICODE,
    )
    encoded = xmtpv3.encode_reaction(payload)
    monkeypatch.setattr('xmtp_content_type_reaction.json.loads', lambda _: (_ for _ in ()).throw(ValueError('boom')))
    decoded = codec.decode(EncodedContent(type_id=ContentTypeReaction, parameters={}, content=encoded))
    assert decoded.content == 'smile'


def test_reaction_codec_should_push_and_fallback() -> None:
    codec = ReactionCodec()
    reaction = Reaction(
        reference='abc',
        reference_inbox_id=None,
        action=ReactionAction.ADDED,
        content=':)',
        schema=ReactionSchema.UNICODE,
    )
    assert codec.should_push(reaction) is False
    assert 'Reacted' in (codec.fallback(reaction) or '')

    reaction_removed = Reaction(
        reference='abc',
        reference_inbox_id=None,
        action=ReactionAction.REMOVED,
        content=':)',
        schema=ReactionSchema.UNICODE,
    )
    assert 'Removed' in (codec.fallback(reaction_removed) or '')


def test_read_receipt_codec() -> None:
    codec = ReadReceiptCodec()
    encoded = codec.encode({})
    assert encoded.type_id == ContentTypeReadReceipt
    assert codec.decode(encoded) == {}
    assert codec.fallback({}) is None
    assert codec.should_push({}) is False


def test_reply_codec_encode_decode() -> None:
    registry = _Registry([TextCodec(), ReplyCodec()])
    reply = Reply(
        reference='abc',
        reference_inbox_id='inbox-id',
        content='pong',
        content_type=ContentTypeText,
    )
    codec = ReplyCodec()
    encoded = codec.encode(reply, registry)
    decoded = codec.decode(encoded, registry)
    assert decoded.reference == 'abc'
    assert decoded.reference_inbox_id == 'inbox-id'
    assert decoded.content == 'pong'
    assert decoded.content_type == ContentTypeText
    assert codec.should_push(reply) is True
    assert codec.fallback(reply) == 'Replied with "pong" to an earlier message'
    reply_non_text = Reply(
        reference='abc',
        reference_inbox_id=None,
        content={'x': 1},
        content_type=ContentTypeText,
    )
    assert codec.fallback(reply_non_text) == 'Replied to an earlier message'
    reply_no_inbox = Reply(
        reference='abc',
        reference_inbox_id=None,
        content='pong',
        content_type=ContentTypeText,
    )
    encoded_no_inbox = codec.encode(reply_no_inbox, registry)
    assert 'referenceInboxId' not in encoded_no_inbox.parameters


def test_reply_codec_requires_registry() -> None:
    codec = ReplyCodec()
    reply = Reply(reference='abc', reference_inbox_id=None, content='hi', content_type=ContentTypeText)
    with pytest.raises(ValueError, match='Codec registry required'):
        codec.encode(reply)
    with pytest.raises(ValueError, match='Codec registry required'):
        codec.decode(EncodedContent(type_id=ContentTypeReply, parameters={}, content=b''))


def test_reply_codec_missing_codec() -> None:
    codec = ReplyCodec()
    registry = _Registry([])
    reply = Reply(reference='abc', reference_inbox_id=None, content='hi', content_type=ContentTypeText)
    with pytest.raises(ValueError, match='Missing codec'):
        codec.encode(reply, registry)


def test_reply_codec_decode_missing_codec(monkeypatch) -> None:
    codec = ReplyCodec()
    registry = _Registry([])

    payload = type('Payload', (), {'reference': 'ref', 'reference_inbox_id': None, 'content': object()})()
    monkeypatch.setattr('xmtp_content_type_reply.xmtpv3.decode_reply', lambda _: payload)
    monkeypatch.setattr(
        'xmtp_content_type_reply._encoded_from_ffi',
        lambda _: EncodedContent(
            type_id=ContentTypeId('xmtp.org', 'missing', 1, 0),
            parameters={},
            content=b'',
        ),
    )

    with pytest.raises(ValueError, match='Missing codec'):
        codec.decode(EncodedContent(type_id=ContentTypeReply, parameters={}, content=b''), registry)


def test_reply_content_type_from_ffi_requires_value() -> None:
    with pytest.raises(ValueError, match='Missing content type'):
        _content_type_from_ffi(None)


def test_attachment_codec_round_trip() -> None:
    codec = AttachmentCodec()
    attachment = Attachment(filename='test.txt', mime_type='text/plain', data=b'hello')
    encoded = codec.encode(attachment)
    assert encoded.type_id == ContentTypeAttachment
    decoded = codec.decode(encoded)
    assert decoded == attachment
    assert codec.fallback(attachment) == "Can't display \"test.txt\". This app doesn't support attachments."
    assert codec.should_push(attachment) is True


def test_attachment_codec_without_filename() -> None:
    codec = AttachmentCodec()
    attachment = Attachment(filename=None, mime_type='text/plain', data=b'hello')
    encoded = codec.encode(attachment)
    assert 'filename' not in encoded.parameters
    assert "Can't display" in (codec.fallback(attachment) or '')


def test_remote_attachment_codec_round_trip() -> None:
    codec = RemoteAttachmentCodec()
    remote = RemoteAttachment(
        url='https://example.com/test',
        content_digest='abc123',
        salt=b'\x01\x02',
        nonce=b'\x03\x04',
        secret=b'\x05\x06',
        scheme='https',
        content_length=10,
        filename='file.txt',
    )
    encoded = codec.encode(remote)
    decoded = codec.decode(encoded)
    assert decoded == remote
    assert codec.should_push(remote) is True
    assert codec.fallback(remote) == "Can't display \"file.txt\". This app doesn't support attachments."


def test_remote_attachment_codec_without_filename() -> None:
    codec = RemoteAttachmentCodec()
    remote = RemoteAttachment(
        url='https://example.com/test',
        content_digest='abc123',
        salt=b'\x01\x02',
        nonce=b'\x03\x04',
        secret=b'\x05\x06',
        scheme='https',
        content_length=10,
        filename=None,
    )
    encoded = codec.encode(remote)
    assert 'filename' not in encoded.parameters
    assert 'attachment' in (codec.fallback(remote) or '')


def test_remote_attachment_requires_https() -> None:
    codec = RemoteAttachmentCodec()
    remote = RemoteAttachment(
        url='http://example.com/test',
        content_digest='abc123',
        salt=b'\x01\x02',
        nonce=b'\x03\x04',
        secret=b'\x05\x06',
        scheme='https',
        content_length=10,
        filename=None,
    )
    with pytest.raises(ValueError, match='Remote attachment URL must use https scheme'):
        codec.encode(remote)


def test_group_updated_codec_decode(monkeypatch) -> None:
    codec = GroupUpdatedCodec()
    sentinel = object()
    monkeypatch.setattr(
        'xmtp_content_type_group_updated.xmtpv3.decode_group_updated',
        lambda payload: sentinel,
    )
    encoded = EncodedContent(type_id=ContentTypeGroupUpdated, parameters={}, content=b'data')
    assert codec.decode(encoded) is sentinel
    with pytest.raises(NotImplementedError):
        codec.encode(sentinel)
    assert codec.should_push(sentinel) is False
    assert codec.fallback(sentinel) is None


def test_transaction_reference_codec_round_trip() -> None:
    codec = TransactionReferenceCodec()
    metadata = TransactionMetadata(
        transaction_type='transfer',
        currency='USDC',
        amount=1.5,
        decimals=6,
        from_address='0xabc',
        to_address='0xdef',
    )
    reference = TransactionReference(
        namespace='eip155',
        network_id='0x1',
        reference='0x123',
        metadata=metadata,
    )
    encoded = codec.encode(reference)
    decoded = codec.decode(encoded)
    assert decoded == reference
    assert codec.should_push(reference) is True
    assert 'transaction hash' in codec.fallback(reference)
    empty_reference = TransactionReference(namespace=None, network_id='1', reference='')
    assert codec.fallback(empty_reference) == 'Crypto transaction'
    no_meta = TransactionReference(namespace='eip155', network_id='1', reference='0x456')
    encoded_no_meta = codec.encode(no_meta)
    decoded_no_meta = codec.decode(encoded_no_meta)
    assert decoded_no_meta.metadata is None


def test_wallet_send_calls_codec_round_trip() -> None:
    codec = WalletSendCallsCodec()
    call = WalletCall(
        to='0xabc',
        data=None,
        value='0x10',
        gas=None,
        metadata=WalletCallMetadata(
            description='Send',
            transaction_type='transfer',
            extra={'currency': 'ETH'},
        ),
    )
    call_no_meta = WalletCall(to='0xdef', data='0x01', value=None, gas='0x1', metadata=None)
    payload = WalletSendCalls(
        version='1.0',
        chain_id='0x1',
        from_address='0xsender',
        calls=[call, call_no_meta],
        capabilities={'foo': 'bar'},
    )
    encoded = codec.encode(payload)
    decoded = codec.decode(encoded)
    assert decoded == payload
    assert codec.should_push(payload) is True
    assert 'Transaction request' in codec.fallback(payload)
    assert decoded.calls[1].metadata is None
