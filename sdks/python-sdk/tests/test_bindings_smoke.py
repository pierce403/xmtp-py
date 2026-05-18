import builtins
import types

import pytest

pytest.importorskip('xmtp_bindings')

from xmtp_bindings import xmtpv3
from xmtp.bindings import (
    _positional_parameter_count,
    check_binding_compatibility,
    get_bindings_version,
    get_native_stream_error_types,
)
from xmtp.errors import BindingCompatibilityError


def test_bindings_startup_compatibility() -> None:
    check_binding_compatibility('0.1.8')
    assert get_bindings_version() == '0.1.8'


def test_bindings_version_fallbacks(monkeypatch) -> None:
    import xmtp.bindings as bindings_module
    import xmtp_bindings

    original_version = getattr(xmtp_bindings, '__version__', None)
    monkeypatch.delattr(xmtp_bindings, '__version__', raising=False)
    monkeypatch.setattr(bindings_module.metadata, 'version', lambda _: 'metadata-version')
    assert get_bindings_version() == 'metadata-version'

    def raise_not_found(_name):
        raise bindings_module.metadata.PackageNotFoundError

    monkeypatch.setattr(bindings_module.metadata, 'version', raise_not_found)
    assert get_bindings_version() is None
    if original_version is not None:
        monkeypatch.setattr(xmtp_bindings, '__version__', original_version, raising=False)


def test_bindings_version_import_error(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'xmtp_bindings':
            raise ImportError('missing')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    assert get_bindings_version() is None


def test_binding_compatibility_errors(monkeypatch) -> None:
    with pytest.raises(BindingCompatibilityError, match='Missing required symbols'):
        check_binding_compatibility(module=types.SimpleNamespace())

    module = types.SimpleNamespace(
        connect_to_backend=lambda a, b, c, d, e, f: None,
        create_client=lambda a, b, c, d, e, f, g, h, i, j, k, l: None,
        get_inbox_id_for_identifier=lambda api, identifier: None,
        generate_inbox_id=lambda identifier, nonce: 'inbox',
        FfiIdentifier=object,
        FfiIdentifierKind=object,
    )
    with pytest.raises(BindingCompatibilityError, match='device sync mode'):
        check_binding_compatibility(module=module)

    module.FfiSyncWorkerMode = object
    module.create_client = lambda a, b, c, d, e, f, g, h, i, j: None
    with pytest.raises(BindingCompatibilityError, match='DbOptions'):
        check_binding_compatibility(module=module)

    module.DbOptions = object
    monkeypatch.setattr('xmtp.bindings.get_bindings_version', lambda: '0.1.5')
    with pytest.raises(BindingCompatibilityError, match='0.1.5'):
        check_binding_compatibility('0.1.8', module=module)


def test_binding_compatibility_import_error(monkeypatch) -> None:
    import xmtp.bindings as bindings_module

    def raise_import_error(_module):
        raise ImportError('native missing')

    monkeypatch.setattr(bindings_module, '_require_symbols', raise_import_error)
    with pytest.raises(BindingCompatibilityError, match='native missing'):
        check_binding_compatibility(module=types.SimpleNamespace())


def test_positional_parameter_count_uninspectable(monkeypatch) -> None:
    import xmtp.bindings as bindings_module

    monkeypatch.setattr(bindings_module.inspect, 'signature', lambda _symbol: (_ for _ in ()).throw(ValueError))
    assert _positional_parameter_count(object()) is None


def test_positional_parameter_count_skips_unhandled_parameter_kinds() -> None:
    def kwargs_only(**kwargs):
        return kwargs

    assert _positional_parameter_count(kwargs_only) == 0


def test_native_stream_error_type_fallbacks(monkeypatch, fake_bindings) -> None:
    class FfiError(Exception):
        pass

    fake_bindings.FfiError = FfiError
    fake_bindings.InternalError = object
    monkeypatch.setattr('xmtp.bindings.NativeBindings', fake_bindings)

    assert get_native_stream_error_types() == (fake_bindings.FfiSubscribeError, FfiError)


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
