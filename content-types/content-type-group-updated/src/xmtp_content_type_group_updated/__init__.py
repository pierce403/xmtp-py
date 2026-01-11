"""Group updated content type for XMTP."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias
from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3
    GroupUpdated: TypeAlias = xmtpv3.FfiGroupUpdated
else:
    GroupUpdated: TypeAlias = object


def _bindings() -> "xmtpv3":
    from xmtp_bindings import xmtpv3

    return xmtpv3


ContentTypeGroupUpdated = ContentTypeId(
    authority_id='xmtp.org',
    type_id='group_updated',
    version_major=1,
    version_minor=0,
)

class GroupUpdatedCodec(ContentCodec[GroupUpdated]):
    """Codec for group updated messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeGroupUpdated

    def encode(self, content: GroupUpdated, registry: CodecRegistry | None = None) -> EncodedContent:
        raise NotImplementedError('GroupUpdated messages are system generated and cannot be encoded')

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> GroupUpdated:
        return _bindings().decode_group_updated(content.content)

    def fallback(self, content: GroupUpdated) -> str | None:
        return None

    def should_push(self, content: GroupUpdated) -> bool:
        return False


__all__ = ['ContentTypeGroupUpdated', 'GroupUpdated', 'GroupUpdatedCodec']
