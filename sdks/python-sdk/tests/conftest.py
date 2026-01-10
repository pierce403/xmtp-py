from __future__ import annotations

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


class FfiReactionAction(str, Enum):
    ADDED = 'added'
    REMOVED = 'removed'


class FfiReactionSchema(str, Enum):
    UNICODE = 'unicode'
    SHORTCODE = 'shortcode'
    CUSTOM = 'custom'


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
        FfiReactionAction=FfiReactionAction,
        FfiReactionSchema=FfiReactionSchema,
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
