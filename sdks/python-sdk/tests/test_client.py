from __future__ import annotations

import builtins
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pytest

from xmtp import Client
from xmtp.client import (
    _SendMessageOpts,
    _callable_accepts_varargs,
    _callable_parameter_names,
    _connect_to_backend,
    _content_type_from_ffi,
    _create_client,
    _default_send_opts,
    _make_db_options,
    _encoded_from_ffi,
    _identifier_to_ffi,
)
from xmtp.errors import (
    BindingCompatibilityError,
    ClientNotInitializedError,
    CodecNotFoundError,
    DatabaseOpenError,
    SignerUnavailableError,
)
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.signers.base import SignerType
from xmtp.types import ClientOptions
from xmtp_content_type_primitives import ContentTypeId, EncodedContent
from xmtp_content_type_text import ContentTypeText, TextCodec


@dataclass
class _FakeSignatureRequest:
    signature_text_value: str
    ecdsa_signature: bytes | None = None
    scw_signature: tuple[bytes, str, int, int | None] | None = None

    def signature_text(self) -> str:
        return self.signature_text_value

    async def add_ecdsa_signature(self, signature: bytes) -> None:
        self.ecdsa_signature = signature

    async def add_scw_signature(
        self, signature: bytes, address: str, chain_id: int, block_number: int | None
    ) -> None:
        self.scw_signature = (signature, address, chain_id, block_number)


@dataclass
class _AsyncSignatureRequest:
    signature_text_value: str
    ecdsa_signature: bytes | None = None
    scw_signature: tuple[bytes, str, int, int | None] | None = None

    async def signature_text(self) -> str:
        return self.signature_text_value

    async def add_ecdsa_signature(self, signature: bytes) -> None:
        self.ecdsa_signature = signature

    async def add_scw_signature(
        self, signature: bytes, address: str, chain_id: int, block_number: int | None
    ) -> None:
        self.scw_signature = (signature, address, chain_id, block_number)


class _FakeClient:
    def __init__(self) -> None:
        self._signature_request: _FakeSignatureRequest | None = None
        self.registered = False
        self._inbox_id = 'inbox-id'
        self._installation_id = b'install-id'
        self._conversations = object()

    def conversations(self) -> object:
        return self._conversations

    def inbox_id(self) -> str:
        return self._inbox_id

    def installation_id(self) -> bytes:
        return self._installation_id

    def signature_request(self) -> _FakeSignatureRequest | None:
        return self._signature_request

    async def register_identity(self, request: _FakeSignatureRequest) -> None:
        self.registered = True

    async def can_message(self, identifiers: list[Any]) -> dict[Any, bool]:
        return {identifier: True for identifier in identifiers}

    async def find_inbox_id(self, identifier: Any) -> str | None:
        return f'inbox-for-{identifier.identifier}'

    def enriched_message(self, message_id: bytes) -> object:
        raise RuntimeError('not used')

    async def sync_preferences(self) -> None:
        return None

    async def inbox_state(self, refresh_from_network: bool) -> Any:
        return {'refresh': refresh_from_network}

    async def get_latest_inbox_state(self, inbox_id: str) -> Any:
        return {'inbox_id': inbox_id}

    async def addresses_from_inbox_id(
        self, refresh_from_network: bool, inbox_ids: list[str]
    ) -> list[Any]:
        return [{'inbox_id': inbox_id} for inbox_id in inbox_ids]

    async def set_consent_states(self, records: list[Any]) -> None:
        return None

    async def get_consent_state(self, entity_type: Any, entity: str) -> Any:
        return {'entity_type': entity_type, 'entity': entity}


class _FakeSigner:
    def __init__(self, identifier: Identifier, signer_type: SignerType) -> None:
        self._identifier = identifier
        self.type = signer_type
        self.signed: bytes | None = None

    async def get_identifier(self) -> Identifier:
        return self._identifier

    async def sign_message(self, message: bytes) -> bytes:
        self.signed = message
        return b'signature'

    async def get_address(self) -> str:
        return '0xabc'

    async def get_chain_id(self) -> int:
        return 1

    async def get_block_number(self) -> int | None:
        return 123


class _DummyCodec:
    def __init__(self) -> None:
        self._content_type = ContentTypeId(
            authority_id='xmtp.org',
            type_id='dummy',
            version_major=1,
            version_minor=0,
        )

    @property
    def content_type(self) -> ContentTypeId:
        return self._content_type

    def encode(self, content: Any, registry: Any = None) -> EncodedContent:
        return EncodedContent(type_id=self._content_type, parameters={}, content=b'dummy')

    def decode(self, content: EncodedContent, registry: Any = None) -> Any:
        return content.content

    def fallback(self, content: Any) -> str | None:
        return None

    def should_push(self, content: Any) -> bool:
        return True


def test_identifier_to_ffi(fake_bindings) -> None:
    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
    ffi = _identifier_to_ffi(identifier)
    assert ffi.identifier == '0xabc'
    assert ffi.identifier_kind == fake_bindings.FfiIdentifierKind.ETHEREUM

    identifier = Identifier(kind=IdentifierKind.PASSKEY, value='passkey')
    ffi = _identifier_to_ffi(identifier)
    assert ffi.identifier_kind == fake_bindings.FfiIdentifierKind.PASSKEY


def test_content_type_from_ffi(fake_bindings) -> None:
    ffi = fake_bindings.FfiContentTypeId(
        authority_id='xmtp.org',
        type_id='text',
        version_major=1,
        version_minor=0,
    )
    content_type = _content_type_from_ffi(ffi)
    assert content_type is not None
    assert str(content_type) == 'xmtp.org/text:1.0'
    assert _content_type_from_ffi(None) is None


def test_default_send_opts(fake_bindings) -> None:
    opts = _default_send_opts()
    assert opts.should_push is True


def test_default_send_opts_falls_back(
    fake_bindings, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Boom:
        def __init__(self, **_: object) -> None:
            raise RuntimeError('boom')

    monkeypatch.setattr(fake_bindings, 'FfiSendMessageOpts', _Boom, raising=False)
    opts = _default_send_opts()
    assert isinstance(opts, _SendMessageOpts)


def test_encoded_from_ffi(fake_bindings) -> None:
    ffi = fake_bindings.FfiEncodedContent(
        type_id=None,
        parameters={},
        fallback=None,
        compression=None,
        content=b'',
    )
    with pytest.raises(ValueError, match='Missing content type'):
        _encoded_from_ffi(ffi)

    ffi = fake_bindings.FfiEncodedContent(
        type_id=fake_bindings.FfiContentTypeId(
            authority_id='xmtp.org',
            type_id='text',
            version_major=1,
            version_minor=0,
        ),
        parameters={'encoding': 'UTF-8'},
        fallback='fallback',
        compression=None,
        content=b'payload',
    )
    encoded = _encoded_from_ffi(ffi)
    assert encoded.parameters['encoding'] == 'UTF-8'
    assert encoded.fallback == 'fallback'


def test_register_default_codecs_import_error(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith('xmtp_content_type_'):
            raise ImportError('blocked')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    client = Client()
    assert client.codec_for(ContentTypeText) is None


def test_register_default_codecs_missing_bindings(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'xmtp_bindings':
            raise ImportError('blocked')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    monkeypatch.delitem(sys.modules, 'xmtp_bindings', raising=False)
    monkeypatch.delitem(sys.modules, 'xmtp_bindings.xmtpv3', raising=False)

    client = Client()
    assert client.codec_for(ContentTypeText) is None


def test_client_registers_default_codecs() -> None:
    pytest.importorskip('xmtp_bindings')
    client = Client()
    assert client.codec_for(ContentTypeText) is not None


def test_client_encode_content_missing_codec() -> None:
    client = Client()
    client._codecs.clear()
    with pytest.raises(CodecNotFoundError):
        client.encode_content('hi', ContentTypeText)


def test_client_encode_content_success() -> None:
    client = Client()
    dummy = _DummyCodec()
    client.register_codec(dummy)
    assert client.codec_for(dummy.content_type) is dummy
    assert client.codec_for(str(dummy.content_type)) is dummy
    assert client.encode_content('payload', dummy.content_type) == b'dummy'


def test_client_prepare_for_send_missing_codec() -> None:
    client = Client()
    client._codecs.clear()
    with pytest.raises(CodecNotFoundError):
        client.prepare_for_send('hi', ContentTypeText)


def test_client_prepare_for_send_uses_should_push() -> None:
    class _NoPushCodec(_DummyCodec):
        def should_push(self, content: Any) -> bool:
            return False

    client = Client()
    codec = _NoPushCodec()
    client.register_codec(codec)
    payload, opts = client.prepare_for_send('payload', codec.content_type)
    assert payload == b'dummy'
    assert opts.should_push is False


def test_client_register_codecs() -> None:
    client = Client()
    dummy = _DummyCodec()
    client.register_codecs([dummy])
    assert client.codec_for(dummy.content_type) is dummy


@pytest.mark.asyncio
async def test_client_register_requires_initialized_client() -> None:
    client = Client()
    with pytest.raises(ClientNotInitializedError):
        await client.register()


@pytest.mark.asyncio
async def test_client_register_requires_signer(fake_bindings) -> None:
    client = Client()
    client._client = _FakeClient()
    with pytest.raises(SignerUnavailableError):
        await client.register()


@pytest.mark.asyncio
async def test_client_register_noop_when_registered(fake_bindings) -> None:
    client = Client()
    fake_client = _FakeClient()
    fake_client._signature_request = None
    client._client = fake_client
    client._signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)
    await client.register()
    assert fake_client.registered is False


@pytest.mark.asyncio
async def test_client_register_eoa(fake_bindings) -> None:
    client = Client()
    fake_client = _FakeClient()
    fake_client._signature_request = _FakeSignatureRequest('sign-me')
    client._client = fake_client
    client._signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)

    await client.register()

    assert fake_client._signature_request.ecdsa_signature == b'signature'
    assert fake_client.registered is True


@pytest.mark.asyncio
async def test_client_register_scw(fake_bindings) -> None:
    client = Client()
    fake_client = _FakeClient()
    fake_client._signature_request = _FakeSignatureRequest('sign-me')
    client._client = fake_client
    client._signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.SCW)

    await client.register()

    assert fake_client._signature_request.scw_signature == (b'signature', '0xabc', 1, 123)
    assert fake_client.registered is True


@pytest.mark.asyncio
async def test_client_register_async_signature_text(fake_bindings) -> None:
    client = Client()
    fake_client = _FakeClient()
    fake_client._signature_request = _AsyncSignatureRequest('sign me')
    client._client = fake_client
    client._signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)

    await client.register()

    assert fake_client.registered is True
    assert client._signer.signed == b'sign me'


@pytest.mark.asyncio
async def test_client_can_message_and_inbox_lookup(fake_bindings) -> None:
    client = Client()
    fake_client = _FakeClient()
    client._client = fake_client

    result = await client.can_message([
        Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
    ])
    assert result == {'0xabc': True}

    inbox_id = await client.get_inbox_id_by_identifier(
        Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
    )
    assert inbox_id == 'inbox-for-0xabc'


@pytest.mark.asyncio
async def test_client_can_message_requires_init() -> None:
    client = Client()
    with pytest.raises(ClientNotInitializedError):
        await client.can_message([])


@pytest.mark.asyncio
async def test_client_get_inbox_requires_init() -> None:
    client = Client()
    with pytest.raises(ClientNotInitializedError):
        await client.get_inbox_id_by_identifier(Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc'))


@pytest.mark.asyncio
async def test_client_build_initializes(fake_bindings, monkeypatch) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    async def connect_to_backend(
        host,
        gateway_host,
        is_secure,
        client_mode,
        app_version,
        auth_callback,
        auth_handle,
    ):
        args = (host, gateway_host, is_secure, client_mode, app_version, auth_callback, auth_handle)
        calls.setdefault('connect', []).append(args)
        return 'api'

    async def get_inbox_id_for_identifier(api, identifier):
        calls['get_inbox_id'] = (api, identifier)
        return None

    def generate_inbox_id(identifier, nonce):
        calls['generate_inbox_id'] = (identifier, nonce)
        return 'generated-inbox'

    async def create_client(*args):
        calls['create_client'] = args
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = generate_inbox_id
    fake_bindings.create_client = create_client

    options = ClientOptions(env='dev', db_path='auto')
    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), options)

    assert client.inbox_id == 'inbox-id'
    assert calls['generate_inbox_id'][1] == 0
    assert calls['create_client'][2].endswith(
        os.path.join(os.getcwd(), 'xmtp-dev-generated-inbox.db3')
    )


@pytest.mark.asyncio
async def test_client_build_with_history_sync(fake_bindings) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    async def connect_to_backend(*args):
        calls.setdefault('connect', []).append(args)
        return f'api-{len(calls["connect"])}'

    async def get_inbox_id_for_identifier(api, identifier):
        return 'existing-inbox'

    async def create_client(*args):
        calls['create_client'] = args
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = lambda identifier, nonce: 'unused'
    fake_bindings.create_client = create_client

    options = ClientOptions(
        env='dev',
        history_sync_url='https://history',
        disable_history_sync=False,
        db_path=lambda inbox_id: f'/tmp/{inbox_id}.db',
        disable_device_sync=True,
        db_encryption_key='0x' + '2' * 64,
    )

    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), options)
    assert client._client is fake_client
    assert len(calls['connect']) == 2
    assert calls['create_client'][2] == '/tmp/existing-inbox.db'
    assert calls['create_client'][9] == fake_bindings.FfiSyncWorkerMode.DISABLED


@pytest.mark.asyncio
async def test_client_build_with_explicit_db_path(fake_bindings) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    async def connect_to_backend(*args):
        calls.setdefault('connect', []).append(args)
        return 'api'

    async def get_inbox_id_for_identifier(api, identifier):
        return 'explicit-inbox'

    async def create_client(*args):
        calls['create_client'] = args
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = lambda identifier, nonce: 'unused'
    fake_bindings.create_client = create_client

    options = ClientOptions(env='dev', db_path='/tmp/static.db')
    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), options)
    assert client._client is fake_client
    assert calls['create_client'][2] == '/tmp/static.db'


@pytest.mark.asyncio
async def test_client_build_with_empty_history_sync(fake_bindings) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    async def connect_to_backend(*args):
        calls.setdefault('connect', []).append(args)
        return 'api'

    async def get_inbox_id_for_identifier(api, identifier):
        return 'inbox'

    async def create_client(*args):
        calls['create_client'] = args
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = lambda identifier, nonce: 'unused'
    fake_bindings.create_client = create_client

    options = ClientOptions(env='dev', history_sync_url='', disable_history_sync=False)
    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), options)
    assert client._client is fake_client
    assert len(calls['connect']) == 1
    assert calls['create_client'][1] == 'api'
    assert calls['create_client'][8] is None


@pytest.mark.asyncio
async def test_client_build_connect_to_backend_six_args(fake_bindings) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    async def connect_to_backend(host, is_secure, client_mode, app_version, auth_callback, auth_handle):
        calls['connect'] = (host, is_secure, client_mode, app_version, auth_callback, auth_handle)
        return 'api'

    async def get_inbox_id_for_identifier(api, identifier):
        return 'inbox'

    async def create_client(*args):
        calls['create_client'] = args
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = lambda identifier, nonce: 'unused'
    fake_bindings.create_client = create_client

    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), ClientOptions())

    assert client._client is fake_client
    assert calls['connect'][0] == ClientOptions().resolved_api_url()
    assert calls['connect'][1] is True


@pytest.mark.asyncio
async def test_client_build_create_client_db_options_and_device_sync_mode(fake_bindings) -> None:
    fake_client = _FakeClient()
    calls: dict[str, Any] = {}

    @dataclass
    class DbOptions:
        db_path: str | None
        encryption_key: bytes | None

    class FfiDeviceSyncMode(str, Enum):
        ENABLED = 'enabled'
        DISABLED = 'disabled'

    async def connect_to_backend(*args):
        return 'api'

    async def get_inbox_id_for_identifier(api, identifier):
        return 'inbox'

    async def create_client(
        api,
        sync_api,
        db_options,
        inbox_id,
        account_identifier,
        nonce,
        legacy_signed_private_key_proto,
        device_sync_server_url,
        device_sync_mode,
        fork_recovery_opts,
    ):
        calls['create_client'] = (
            api,
            sync_api,
            db_options,
            inbox_id,
            account_identifier,
            nonce,
            legacy_signed_private_key_proto,
            device_sync_server_url,
            device_sync_mode,
            fork_recovery_opts,
        )
        return fake_client

    fake_bindings.connect_to_backend = connect_to_backend
    fake_bindings.get_inbox_id_for_identifier = get_inbox_id_for_identifier
    fake_bindings.generate_inbox_id = lambda identifier, nonce: 'unused'
    fake_bindings.create_client = create_client
    fake_bindings.DbOptions = DbOptions
    fake_bindings.FfiDeviceSyncMode = FfiDeviceSyncMode
    del fake_bindings.FfiSyncWorkerMode

    options = ClientOptions(
        db_path='dev.db3',
        db_encryption_key='0x' + '1' * 64,
        disable_device_sync=True,
    )
    client = await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), options)

    assert client._client is fake_client
    assert calls['create_client'][2] == DbOptions(db_path='dev.db3', encryption_key=b'\x11' * 32)
    assert calls['create_client'][8] == FfiDeviceSyncMode.DISABLED


@pytest.mark.asyncio
async def test_client_build_rejects_incompatible_bindings(fake_bindings) -> None:
    fake_bindings.connect_to_backend = lambda *args: object()
    fake_bindings.get_inbox_id_for_identifier = lambda *args: None
    fake_bindings.generate_inbox_id = lambda *args: 'inbox'

    async def create_client(api, sync_api, db, encryption_key, inbox_id):
        return _FakeClient()

    fake_bindings.create_client = create_client

    with pytest.raises(BindingCompatibilityError, match='create_client accepts 5 args'):
        await Client.build(Identifier(IdentifierKind.ETHEREUM, '0xabc'), ClientOptions())


def test_client_exposes_sdk_and_bindings_versions() -> None:
    import xmtp

    assert xmtp.__version__ == '0.1.7'
    assert hasattr(xmtp, '__bindings_version__')


def test_callable_signature_helpers_handle_uninspectable(monkeypatch) -> None:
    import xmtp.client as client_module

    def raise_signature(_func):
        raise ValueError('no signature')

    monkeypatch.setattr(client_module.inspect, 'signature', raise_signature)
    assert _callable_accepts_varargs(object()) is True
    assert _callable_parameter_names(object()) is None

    monkeypatch.setattr(client_module, '_callable_accepts_varargs', lambda _func: False)
    assert _callable_parameter_names(object()) is None


@pytest.mark.asyncio
async def test_connect_to_backend_type_error_fallbacks(fake_bindings) -> None:
    calls: list[tuple[Any, ...]] = []

    async def connect_to_backend(*args):
        calls.append(args)
        if len(args) == 7:
            raise TypeError('too many args')
        if args[1] is True:
            raise TypeError('wrong six arg shape')
        return 'api'

    fake_bindings.connect_to_backend = connect_to_backend

    result = await _connect_to_backend('host', 'gateway', True, 'app')

    assert result == 'api'
    assert len(calls) == 3
    assert calls[-1] == ('host', 'gateway', True, None, 'app', None)


@pytest.mark.asyncio
async def test_connect_to_backend_reraises_original_type_error(fake_bindings) -> None:
    original_error = TypeError('too many args')

    async def connect_to_backend(*args):
        if len(args) == 7:
            raise original_error
        raise TypeError('still wrong')

    fake_bindings.connect_to_backend = connect_to_backend

    with pytest.raises(TypeError) as exc_info:
        await _connect_to_backend('host', 'gateway', True, 'app')
    assert exc_info.value is original_error


@pytest.mark.asyncio
async def test_connect_to_backend_unknown_signature_uses_legacy_call(fake_bindings) -> None:
    import xmtp.client as client_module

    calls: list[tuple[Any, ...]] = []

    class Connect:
        __signature__ = client_module.inspect.Signature(
            [
                client_module.inspect.Parameter(
                    'host',
                    client_module.inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
                client_module.inspect.Parameter(
                    'is_secure',
                    client_module.inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
                client_module.inspect.Parameter(
                    'client_mode',
                    client_module.inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
                client_module.inspect.Parameter(
                    'app_version',
                    client_module.inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
                client_module.inspect.Parameter(
                    'auth_callback',
                    client_module.inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
            ]
        )

        async def __call__(self, *args):
            calls.append(args)
            return 'api'

    fake_bindings.connect_to_backend = Connect()

    result = await _connect_to_backend('host', 'gateway', True, 'app')

    assert result == 'api'
    assert calls == [('host', 'gateway', True, None, 'app', None, None)]


def test_make_db_options_fallback_constructors(fake_bindings) -> None:
    class DbOptions:
        def __init__(self, *args, **kwargs) -> None:
            if kwargs:
                raise TypeError('no kwargs')
            self.args = args

    fake_bindings.DbOptions = DbOptions

    options = _make_db_options('path.db3', b'key')

    assert options.args == ('path.db3', b'key')


def test_make_db_options_uses_candidate_kwargs_when_signature_has_no_known_names(
    fake_bindings,
) -> None:
    class DbOptions:
        def __init__(self, ignored=None, **kwargs) -> None:
            self.ignored = ignored
            self.kwargs = kwargs

    fake_bindings.FfiDbOptions = DbOptions

    options = _make_db_options('path.db3', b'key')

    assert options.kwargs == {'db_path': 'path.db3', 'encryption_key': b'key'}


def test_make_db_options_requires_native_class(fake_bindings) -> None:
    if hasattr(fake_bindings, 'DbOptions'):
        del fake_bindings.DbOptions
    if hasattr(fake_bindings, 'FfiDbOptions'):
        del fake_bindings.FfiDbOptions

    with pytest.raises(TypeError, match='DbOptions is unavailable'):
        _make_db_options('path.db3', None)


@pytest.mark.asyncio
async def test_create_client_explicit_legacy_signature(fake_bindings) -> None:
    calls: dict[str, tuple[Any, ...]] = {}

    async def create_client(
        api,
        sync_api,
        db,
        encryption_key,
        inbox_id,
        account_identifier,
        nonce,
        legacy_signed_private_key_proto,
        device_sync_server_url,
        device_sync_mode,
        allow_offline,
        fork_recovery_opts,
    ):
        calls['create_client'] = (
            api,
            sync_api,
            db,
            encryption_key,
            inbox_id,
            account_identifier,
            nonce,
            legacy_signed_private_key_proto,
            device_sync_server_url,
            device_sync_mode,
            allow_offline,
            fork_recovery_opts,
        )
        return 'client'

    fake_bindings.create_client = create_client

    result = await _create_client(
        'api',
        'sync',
        'path.db3',
        b'key',
        'inbox',
        'identifier',
        1,
        None,
        fake_bindings.FfiSyncWorkerMode.DISABLED,
    )

    assert result == 'client'
    assert calls['create_client'][2] == 'path.db3'


@pytest.mark.asyncio
async def test_create_client_rejects_unknown_parameters(fake_bindings) -> None:
    @dataclass
    class DbOptions:
        db_path: str | None
        encryption_key: bytes | None

    async def create_client(api, sync_api, db_options, surprise):
        return object()

    fake_bindings.create_client = create_client
    fake_bindings.DbOptions = DbOptions

    with pytest.raises(TypeError, match='Unsupported create_client parameters'):
        await _create_client(
            'api',
            'sync',
            'path.db3',
            None,
            'inbox',
            'identifier',
            1,
            None,
            fake_bindings.FfiSyncWorkerMode.DISABLED,
        )


def test_client_properties_without_init() -> None:
    client = Client()
    assert client.inbox_id is None
    assert client.installation_id is None
    assert client.is_registered is False
    with pytest.raises(ClientNotInitializedError):
        _ = client.conversations
    with pytest.raises(ClientNotInitializedError):
        _ = client.preferences


def test_client_properties_with_init() -> None:
    client = Client()
    fake_client = _FakeClient()
    client._client = fake_client
    client._conversations = object()
    client._preferences = object()
    assert client.installation_id == b'install-id'
    assert client.conversations is client._conversations
    assert client.preferences is client._preferences


def test_client_options_and_account_identifier() -> None:
    options = ClientOptions(env='local')
    client = Client(options)
    assert client.options.env == 'local'
    assert client.account_identifier is None


def test_client_registers_option_codecs() -> None:
    dummy = _DummyCodec()
    client = Client(ClientOptions(codecs=[dummy]))
    assert client.codec_for(dummy.content_type) is dummy


def test_client_is_registered() -> None:
    client = Client()
    fake_client = _FakeClient()
    fake_client._signature_request = _FakeSignatureRequest('sign')
    client._client = fake_client
    assert client.is_registered is False
    fake_client._signature_request = None
    assert client.is_registered is True


@pytest.mark.asyncio
async def test_client_create_from_env(monkeypatch) -> None:
    fake_signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)

    async def fake_init(self, identifier):
        self._client = _FakeClient()
        self._identifier = identifier

    async def fake_register(self):
        self._registered = True

    monkeypatch.setattr('xmtp.client.load_signer_from_env', lambda: fake_signer)
    monkeypatch.setattr('xmtp.client.load_client_options_from_env', lambda opts=None: ClientOptions())
    monkeypatch.setattr(Client, '_init', fake_init, raising=True)
    monkeypatch.setattr(Client, 'register', fake_register, raising=True)

    client = await Client.create_from_env()
    assert client._client is not None
    assert client.account_identifier == await fake_signer.get_identifier()


@pytest.mark.asyncio
async def test_client_from_env_alias(monkeypatch) -> None:
    called = {'count': 0}

    async def fake_create_from_env(cls, options=None):
        called['count'] += 1
        return Client()

    monkeypatch.setattr(Client, 'create_from_env', classmethod(fake_create_from_env))
    client = await Client.from_env()
    assert isinstance(client, Client)
    assert called['count'] == 1


@pytest.mark.asyncio
async def test_client_init_noop_when_initialized(fake_bindings) -> None:
    client = Client()
    client._client = object()

    def connect_to_backend(*args, **kwargs):
        raise RuntimeError('should not be called')

    fake_bindings.connect_to_backend = connect_to_backend
    await client._init(Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc'))


@pytest.mark.asyncio
async def test_client_init_db_error(monkeypatch) -> None:
    class _Bindings:
        class FfiIdentifierKind(str, Enum):
            ETHEREUM = 'ethereum'
            PASSKEY = 'passkey'

        @dataclass(frozen=True)
        class FfiIdentifier:
            identifier: str
            identifier_kind: "_Bindings.FfiIdentifierKind"

        class FfiSyncWorkerMode(str, Enum):
            DISABLED = 'disabled'
            ENABLED = 'enabled'

        @staticmethod
        async def connect_to_backend(*args, **kwargs):
            return object()

        @staticmethod
        async def get_inbox_id_for_identifier(*args, **kwargs):
            return None

        @staticmethod
        def generate_inbox_id(*args, **kwargs):
            return 'inbox'

        @staticmethod
        async def create_client(*args, **kwargs):
            raise RuntimeError('sqlcipher failure')

    monkeypatch.setattr('xmtp.client.NativeBindings', _Bindings, raising=False)

    client = Client()
    with pytest.raises(DatabaseOpenError, match='SQLCipher'):
        await client._init(Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc'))


@pytest.mark.asyncio
async def test_client_init_non_db_error(monkeypatch) -> None:
    class _Bindings:
        class FfiIdentifierKind(str, Enum):
            ETHEREUM = 'ethereum'
            PASSKEY = 'passkey'

        @dataclass(frozen=True)
        class FfiIdentifier:
            identifier: str
            identifier_kind: "_Bindings.FfiIdentifierKind"

        class FfiSyncWorkerMode(str, Enum):
            DISABLED = 'disabled'
            ENABLED = 'enabled'

        @staticmethod
        async def connect_to_backend(*args, **kwargs):
            return object()

        @staticmethod
        async def get_inbox_id_for_identifier(*args, **kwargs):
            return None

        @staticmethod
        def generate_inbox_id(*args, **kwargs):
            return 'inbox'

        @staticmethod
        async def create_client(*args, **kwargs):
            raise RuntimeError('boom')

    monkeypatch.setattr('xmtp.client.NativeBindings', _Bindings, raising=False)

    client = Client()
    with pytest.raises(RuntimeError, match='boom'):
        await client._init(Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc'))


@pytest.mark.asyncio
async def test_client_create_disable_auto_register(monkeypatch) -> None:
    async def fake_init(self, identifier):
        self._client = _FakeClient()
        self._identifier = identifier

    called = {'register': 0}

    async def fake_register(self):
        called['register'] += 1

    monkeypatch.setattr(Client, '_init', fake_init, raising=True)
    monkeypatch.setattr(Client, 'register', fake_register, raising=True)

    signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)
    options = ClientOptions(disable_auto_register=True)
    client = await Client.create(signer, options)
    assert client._client is not None
    assert called['register'] == 0


@pytest.mark.asyncio
async def test_client_create_auto_register(monkeypatch) -> None:
    async def fake_init(self, identifier):
        self._client = _FakeClient()
        self._identifier = identifier

    called = {'register': 0}

    async def fake_register(self):
        called['register'] += 1

    monkeypatch.setattr(Client, '_init', fake_init, raising=True)
    monkeypatch.setattr(Client, 'register', fake_register, raising=True)

    signer = _FakeSigner(Identifier(IdentifierKind.ETHEREUM, '0xabc'), SignerType.EOA)
    options = ClientOptions(disable_auto_register=False)
    client = await Client.create(signer, options)
    assert client._client is not None
    assert called['register'] == 1
