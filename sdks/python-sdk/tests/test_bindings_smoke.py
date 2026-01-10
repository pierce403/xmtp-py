import pytest

pytest.importorskip('xmtp_bindings')

from xmtp_bindings import xmtpv3


def test_bindings_encode_decode_text() -> None:
    encoded = xmtpv3.encode_text('hi')
    assert xmtpv3.decode_text(encoded) == 'hi'


def test_bindings_encode_decode_markdown() -> None:
    encoded = xmtpv3.encode_markdown('*hi*')
    assert xmtpv3.decode_markdown(encoded) == '*hi*'


def test_bindings_read_receipt() -> None:
    encoded = xmtpv3.encode_read_receipt(xmtpv3.FfiReadReceipt())
    decoded = xmtpv3.decode_read_receipt(encoded)
    assert isinstance(decoded, xmtpv3.FfiReadReceipt)


def test_bindings_reaction_round_trip() -> None:
    payload = xmtpv3.FfiReactionPayload(
        reference='ref',
        reference_inbox_id='inbox',
        action=xmtpv3.FfiReactionAction.ADDED,
        content='smile',
        schema=xmtpv3.FfiReactionSchema.UNICODE,
    )
    encoded = xmtpv3.encode_reaction(payload)
    decoded = xmtpv3.decode_reaction(encoded)
    assert decoded.reference == 'ref'
    assert decoded.content == 'smile'


def test_bindings_attachment_round_trip() -> None:
    payload = xmtpv3.FfiAttachment(filename='file.txt', mime_type='text/plain', content=b'data')
    encoded = xmtpv3.encode_attachment(payload)
    decoded = xmtpv3.decode_attachment(encoded)
    assert decoded.filename == 'file.txt'
    assert decoded.mime_type == 'text/plain'
    assert decoded.content == b'data'


def test_bindings_remote_attachment_round_trip() -> None:
    payload = xmtpv3.FfiRemoteAttachment(
        url='https://example.com',
        content_digest='digest',
        secret=b'secret',
        salt=b'salt',
        nonce=b'nonce',
        scheme='https',
        content_length=10,
        filename='file.txt',
    )
    encoded = xmtpv3.encode_remote_attachment(payload)
    decoded = xmtpv3.decode_remote_attachment(encoded)
    assert decoded.url == 'https://example.com'
    assert decoded.filename == 'file.txt'


def test_bindings_transaction_reference_round_trip() -> None:
    metadata = xmtpv3.FfiTransactionMetadata(
        transaction_type='transfer',
        currency='ETH',
        amount=1.0,
        decimals=18,
        from_address='0xabc',
        to_address='0xdef',
    )
    payload = xmtpv3.FfiTransactionReference(
        namespace='eip155',
        network_id='1',
        reference='0x123',
        metadata=metadata,
    )
    encoded = xmtpv3.encode_transaction_reference(payload)
    decoded = xmtpv3.decode_transaction_reference(encoded)
    assert decoded.reference == '0x123'
    assert decoded.metadata is not None


def test_bindings_wallet_send_calls_round_trip() -> None:
    metadata = xmtpv3.FfiWalletCallMetadata(
        description='Send',
        transaction_type='transfer',
        extra={'foo': 'bar'},
    )
    call = xmtpv3.FfiWalletCall(
        to='0xabc',
        data=None,
        value='0x1',
        gas=None,
        metadata=metadata,
    )
    payload = xmtpv3.FfiWalletSendCalls(
        version='1.0',
        chain_id='1',
        _from='0xdef',
        calls=[call],
        capabilities={'cap': '1'},
    )
    encoded = xmtpv3.encode_wallet_send_calls(payload)
    decoded = xmtpv3.decode_wallet_send_calls(encoded)
    assert decoded.version == '1.0'
    assert decoded.calls[0].metadata is not None
