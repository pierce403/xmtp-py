from __future__ import annotations

import pickle
import sys
import types
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pytest


class FfiIdentifierKind(str, Enum):
    ETHEREUM = 'ethereum'
    PASSKEY = 'passkey'


@dataclass(frozen=True)
class FfiIdentifier:
    identifier: str
    identifier_kind: FfiIdentifierKind


@dataclass
class FfiSendMessageOpts:
    should_push: bool


@dataclass
class FfiContentTypeId:
    authority_id: str
    type_id: str
    version_major: int
    version_minor: int


@dataclass
class FfiEncodedContent:
    type_id: FfiContentTypeId | None
    parameters: dict[str, str]
    fallback: str | None
    compression: int | None
    content: bytes


class FfiConversationType(str, Enum):
    DM = 'dm'
    GROUP = 'group'


class FfiConsentState(str, Enum):
    ALLOWED = 'allowed'
    DENIED = 'denied'
    UNKNOWN = 'unknown'


class FfiGroupQueryOrderBy(str, Enum):
    LAST_ACTIVITY = 'last_activity'
    CREATED_AT = 'created_at'


@dataclass
class FfiCreateDmOptions:
    message_disappearing_settings: object | None


@dataclass
class FfiCreateGroupOptions:
    permissions: object | None
    group_name: str | None
    group_image_url_square: str | None
    group_description: str | None
    custom_permission_policy_set: object | None
    message_disappearing_settings: object | None
    app_data: object | None


@dataclass
class FfiListConversationsOptions:
    created_after_ns: int | None
    created_before_ns: int | None
    last_activity_before_ns: int | None
    last_activity_after_ns: int | None
    order_by: FfiGroupQueryOrderBy | None
    limit: int | None
    consent_states: list[FfiConsentState] | None
    include_duplicate_dms: bool


class FfiSubscribeError(Exception):
    pass


class FfiConversationCallback:
    pass


class FfiMessageCallback:
    pass


class FfiSyncWorkerMode(str, Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'


class FfiDeviceSyncMode(str, Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'


class FfiReactionAction(str, Enum):
    ADDED = 'added'
    REMOVED = 'removed'


class FfiReactionSchema(str, Enum):
    UNICODE = 'unicode'
    SHORTCODE = 'shortcode'
    CUSTOM = 'custom'


@dataclass
class FfiReadReceipt:
    pass


@dataclass
class FfiReactionPayload:
    reference: str
    reference_inbox_id: str
    action: FfiReactionAction
    content: str
    schema: FfiReactionSchema


@dataclass
class FfiAttachment:
    filename: str | None
    mime_type: str
    content: bytes


@dataclass
class FfiRemoteAttachment:
    url: str
    content_digest: str
    secret: bytes
    salt: bytes
    nonce: bytes
    scheme: str
    content_length: int
    filename: str | None


@dataclass
class FfiTransactionMetadata:
    transaction_type: str
    currency: str
    amount: float
    decimals: int
    from_address: str
    to_address: str


@dataclass
class FfiTransactionReference:
    namespace: str | None
    network_id: str
    reference: str
    metadata: FfiTransactionMetadata | None


@dataclass
class FfiWalletCallMetadata:
    description: str
    transaction_type: str
    extra: dict[str, str]


@dataclass
class FfiWalletCall:
    to: str | None
    data: str | None
    value: str | None
    gas: str | None
    metadata: FfiWalletCallMetadata | None


@dataclass
class FfiWalletSendCalls:
    version: str
    chain_id: str
    _from: str
    calls: list[FfiWalletCall]
    capabilities: dict[str, str] | None


@dataclass
class FfiReply:
    reference: str
    reference_inbox_id: str | None
    content: FfiEncodedContent


@dataclass
class FfiGroupUpdated:
    pass


def _pickle_encode(payload: object) -> bytes:
    return pickle.dumps(payload)


def _pickle_decode(payload: bytes) -> object:
    return pickle.loads(payload)


def _install_fake_xmtp_bindings() -> None:
    xmtpv3 = types.ModuleType('xmtp_bindings.xmtpv3')

    xmtpv3.FfiIdentifierKind = FfiIdentifierKind
    xmtpv3.FfiIdentifier = FfiIdentifier
    xmtpv3.FfiSyncWorkerMode = FfiSyncWorkerMode
    xmtpv3.FfiDeviceSyncMode = FfiDeviceSyncMode
    xmtpv3.FfiContentTypeId = FfiContentTypeId
    xmtpv3.FfiEncodedContent = FfiEncodedContent
    xmtpv3.FfiReadReceipt = FfiReadReceipt
    xmtpv3.FfiReactionAction = FfiReactionAction
    xmtpv3.FfiReactionSchema = FfiReactionSchema
    xmtpv3.FfiReactionPayload = FfiReactionPayload
    xmtpv3.FfiAttachment = FfiAttachment
    xmtpv3.FfiRemoteAttachment = FfiRemoteAttachment
    xmtpv3.FfiTransactionMetadata = FfiTransactionMetadata
    xmtpv3.FfiTransactionReference = FfiTransactionReference
    xmtpv3.FfiWalletCallMetadata = FfiWalletCallMetadata
    xmtpv3.FfiWalletCall = FfiWalletCall
    xmtpv3.FfiWalletSendCalls = FfiWalletSendCalls
    xmtpv3.FfiReply = FfiReply
    xmtpv3.FfiGroupUpdated = FfiGroupUpdated

    xmtpv3.encode_text = lambda text: text.encode('utf-8')
    xmtpv3.decode_text = lambda payload: payload.decode('utf-8')
    xmtpv3.encode_markdown = lambda text: text.encode('utf-8')
    xmtpv3.decode_markdown = lambda payload: payload.decode('utf-8')

    xmtpv3.encode_read_receipt = lambda receipt: _pickle_encode(receipt)
    xmtpv3.decode_read_receipt = lambda payload: FfiReadReceipt()

    xmtpv3.encode_reaction = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_reaction = lambda payload: _pickle_decode(payload)

    xmtpv3.encode_attachment = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_attachment = lambda payload: _pickle_decode(payload)

    xmtpv3.encode_remote_attachment = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_remote_attachment = lambda payload: _pickle_decode(payload)

    xmtpv3.encode_transaction_reference = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_transaction_reference = lambda payload: _pickle_decode(payload)

    xmtpv3.encode_wallet_send_calls = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_wallet_send_calls = lambda payload: _pickle_decode(payload)

    xmtpv3.encode_reply = lambda payload: _pickle_encode(payload)
    xmtpv3.decode_reply = lambda payload: _pickle_decode(payload)

    xmtpv3.decode_group_updated = lambda payload: payload

    async def connect_to_backend(*args: object) -> object:
        return object()

    async def create_client(*args: object) -> object:
        return object()

    xmtpv3.connect_to_backend = connect_to_backend
    xmtpv3.create_client = create_client
    xmtpv3.get_inbox_id_for_identifier = lambda api, identifier: 'inbox'
    xmtpv3.generate_inbox_id = lambda identifier, nonce: 'generated-inbox'

    xmtp_bindings = types.ModuleType('xmtp_bindings')
    xmtp_bindings.xmtpv3 = xmtpv3
    xmtp_bindings.__version__ = '0.1.7'

    sys.modules['xmtp_bindings'] = xmtp_bindings
    sys.modules['xmtp_bindings.xmtpv3'] = xmtpv3


def _ensure_xmtp_bindings() -> None:
    try:
        import xmtp_bindings  # noqa: F401
    except ImportError:
        _install_fake_xmtp_bindings()

    try:
        from xmtp_bindings import xmtpv3
    except ImportError:
        return

    for module_name in (
        'xmtp_content_type_group_updated',
        'xmtp_content_type_reaction',
        'xmtp_content_type_reply',
    ):
        try:
            module = __import__(module_name, fromlist=['__dict__'])
        except ImportError:
            continue
        setattr(module, 'xmtpv3', xmtpv3)


_ensure_xmtp_bindings()


class _Bindings(types.SimpleNamespace):
    pass


@pytest.fixture()
def fake_bindings(monkeypatch: pytest.MonkeyPatch):
    bindings = _Bindings(
        FfiIdentifierKind=FfiIdentifierKind,
        FfiIdentifier=FfiIdentifier,
        FfiSendMessageOpts=FfiSendMessageOpts,
        FfiContentTypeId=FfiContentTypeId,
        FfiEncodedContent=FfiEncodedContent,
        FfiConversationType=FfiConversationType,
        FfiConsentState=FfiConsentState,
        FfiGroupQueryOrderBy=FfiGroupQueryOrderBy,
        FfiCreateDmOptions=FfiCreateDmOptions,
        FfiCreateGroupOptions=FfiCreateGroupOptions,
        FfiListConversationsOptions=FfiListConversationsOptions,
        FfiSubscribeError=FfiSubscribeError,
        FfiConversationCallback=FfiConversationCallback,
        FfiMessageCallback=FfiMessageCallback,
        FfiSyncWorkerMode=FfiSyncWorkerMode,
        FfiDeviceSyncMode=FfiDeviceSyncMode,
        FfiReactionAction=FfiReactionAction,
        FfiReactionSchema=FfiReactionSchema,
        FfiReadReceipt=FfiReadReceipt,
    )

    import xmtp.bindings
    import xmtp.client
    import xmtp.conversation
    import xmtp.conversations
    import xmtp.preferences

    for module in (
        xmtp.bindings,
        xmtp.client,
        xmtp.conversation,
        xmtp.conversations,
        xmtp.preferences,
    ):
        monkeypatch.setattr(module, 'NativeBindings', bindings, raising=False)

    return bindings
