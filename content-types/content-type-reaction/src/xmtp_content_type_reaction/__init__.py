"""Reaction content type for XMTP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _FfiReactionAction(Protocol):
    ADDED: object
    REMOVED: object


class _FfiReactionSchema(Protocol):
    UNICODE: object
    SHORTCODE: object
    CUSTOM: object


class _FfiReactionPayload(Protocol):
    def __init__(
        self,
        *,
        reference: str,
        reference_inbox_id: str,
        action: object,
        content: str,
        schema: object,
    ) -> None: ...

    reference: str
    reference_inbox_id: str
    action: object
    content: str
    schema: object


class _Bindings(Protocol):
    FfiReactionAction: type[_FfiReactionAction]
    FfiReactionSchema: type[_FfiReactionSchema]
    FfiReactionPayload: type[_FfiReactionPayload]

    def encode_reaction(self, payload: _FfiReactionPayload) -> bytes: ...

    def decode_reaction(self, data: bytes) -> _FfiReactionPayload: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeReaction = ContentTypeId(
    authority_id="xmtp.org",
    type_id="reaction",
    version_major=1,
    version_minor=0,
)


class ReactionAction(str, Enum):
    ADDED = "added"
    REMOVED = "removed"


class ReactionSchema(str, Enum):
    UNICODE = "unicode"
    SHORTCODE = "shortcode"
    CUSTOM = "custom"


@dataclass(slots=True)
class Reaction:
    reference: str
    reference_inbox_id: str | None
    action: ReactionAction
    content: str
    schema: ReactionSchema


class ReactionCodec(ContentCodec[Reaction]):
    """Codec for reaction messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeReaction

    def encode(self, content: Reaction, registry: CodecRegistry | None = None) -> EncodedContent:
        ffi_action = (
            _bindings().FfiReactionAction.ADDED
            if content.action == ReactionAction.ADDED
            else _bindings().FfiReactionAction.REMOVED
        )
        ffi_schema = {
            ReactionSchema.UNICODE: _bindings().FfiReactionSchema.UNICODE,
            ReactionSchema.SHORTCODE: _bindings().FfiReactionSchema.SHORTCODE,
            ReactionSchema.CUSTOM: _bindings().FfiReactionSchema.CUSTOM,
        }[content.schema]
        payload = _bindings().FfiReactionPayload(
            reference=content.reference,
            reference_inbox_id=content.reference_inbox_id or "",
            action=ffi_action,
            content=content.content,
            schema=ffi_schema,
        )
        encoded = _bindings().encode_reaction(payload)
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> Reaction:
        decoded_text: str | None = None
        if isinstance(content.content, (bytes, bytearray)):
            try:
                decoded_text = bytes(content.content).decode("utf-8")
            except UnicodeDecodeError:
                decoded_text = None

        if decoded_text:
            try:
                payload = json.loads(decoded_text)
                reference_inbox_id = payload.get(
                    "referenceInboxId", payload.get("reference_inbox_id")
                )
                return Reaction(
                    reference=payload["reference"],
                    reference_inbox_id=reference_inbox_id,
                    action=ReactionAction(payload["action"]),
                    content=payload["content"],
                    schema=ReactionSchema(payload["schema"]),
                )
            except (ValueError, KeyError, TypeError):
                pass

        if decoded_text is not None:
            params = content.parameters
            if "action" in params and "reference" in params and "schema" in params:
                return Reaction(
                    reference=params["reference"],
                    reference_inbox_id=None,
                    action=ReactionAction(params["action"]),
                    content=decoded_text,
                    schema=ReactionSchema(params["schema"]),
                )

        payload = _bindings().decode_reaction(content.content)
        action = (
            ReactionAction.ADDED
            if payload.action == _bindings().FfiReactionAction.ADDED
            else ReactionAction.REMOVED
        )
        schema_map = {
            _bindings().FfiReactionSchema.UNICODE: ReactionSchema.UNICODE,
            _bindings().FfiReactionSchema.SHORTCODE: ReactionSchema.SHORTCODE,
            _bindings().FfiReactionSchema.CUSTOM: ReactionSchema.CUSTOM,
        }
        schema = schema_map[payload.schema]
        reference_inbox_id = payload.reference_inbox_id or None
        return Reaction(
            reference=payload.reference,
            reference_inbox_id=reference_inbox_id,
            action=action,
            content=payload.content,
            schema=schema,
        )

    def fallback(self, content: Reaction) -> str | None:
        if content.action == ReactionAction.ADDED:
            return f'Reacted "{content.content}" to an earlier message'
        if content.action == ReactionAction.REMOVED:
            return f'Removed "{content.content}" from an earlier message'
        return None

    def should_push(self, content: Reaction) -> bool:
        return False


__all__ = ["ContentTypeReaction", "Reaction", "ReactionAction", "ReactionSchema", "ReactionCodec"]
