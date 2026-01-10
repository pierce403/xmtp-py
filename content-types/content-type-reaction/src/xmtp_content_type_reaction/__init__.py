"""Reaction content type for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from xmtp_bindings import xmtpv3
from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


ContentTypeReaction = ContentTypeId(
    authority_id='xmtp.org',
    type_id='reaction',
    version_major=1,
    version_minor=0,
)


class ReactionAction(str, Enum):
    ADDED = 'added'
    REMOVED = 'removed'


class ReactionSchema(str, Enum):
    UNICODE = 'unicode'
    SHORTCODE = 'shortcode'
    CUSTOM = 'custom'


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
            xmtpv3.FfiReactionAction.ADDED
            if content.action == ReactionAction.ADDED
            else xmtpv3.FfiReactionAction.REMOVED
        )
        ffi_schema = {
            ReactionSchema.UNICODE: xmtpv3.FfiReactionSchema.UNICODE,
            ReactionSchema.SHORTCODE: xmtpv3.FfiReactionSchema.SHORTCODE,
            ReactionSchema.CUSTOM: xmtpv3.FfiReactionSchema.CUSTOM,
        }[content.schema]
        payload = xmtpv3.FfiReactionPayload(
            reference=content.reference,
            reference_inbox_id=content.reference_inbox_id or '',
            action=ffi_action,
            content=content.content,
            schema=ffi_schema,
        )
        encoded = xmtpv3.encode_reaction(payload)
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> Reaction:
        payload = xmtpv3.decode_reaction(content.content)
        action = (
            ReactionAction.ADDED
            if payload.action == xmtpv3.FfiReactionAction.ADDED
            else ReactionAction.REMOVED
        )
        schema_map = {
            xmtpv3.FfiReactionSchema.UNICODE: ReactionSchema.UNICODE,
            xmtpv3.FfiReactionSchema.SHORTCODE: ReactionSchema.SHORTCODE,
            xmtpv3.FfiReactionSchema.CUSTOM: ReactionSchema.CUSTOM,
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
            return f'Reacted “{content.content}” to an earlier message'
        if content.action == ReactionAction.REMOVED:
            return f'Removed “{content.content}” from an earlier message'
        return None

    def should_push(self, content: Reaction) -> bool:
        return False


__all__ = ['ContentTypeReaction', 'Reaction', 'ReactionAction', 'ReactionSchema', 'ReactionCodec']
