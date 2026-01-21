"""Group updated content type for XMTP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    GroupUpdated: TypeAlias = xmtpv3.FfiGroupUpdated
else:
    GroupUpdated: TypeAlias = object


class _Bindings(Protocol):
    def decode_group_updated(self, data: bytes) -> GroupUpdated: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeGroupUpdated = ContentTypeId(
    authority_id="xmtp.org",
    type_id="group_updated",
    version_major=1,
    version_minor=0,
)


class GroupUpdatedCodec(ContentCodec[GroupUpdated]):
    """Codec for group updated messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeGroupUpdated

    def encode(
        self, content: GroupUpdated, registry: CodecRegistry | None = None
    ) -> EncodedContent:
        raise NotImplementedError(
            "GroupUpdated messages are system generated and cannot be encoded"
        )

    def decode(
        self, content: EncodedContent, registry: CodecRegistry | None = None
    ) -> GroupUpdated:
        return _bindings().decode_group_updated(content.content)

    def fallback(self, content: GroupUpdated) -> str | None:
        return None

    def should_push(self, content: GroupUpdated) -> bool:
        return False


__all__ = ["ContentTypeGroupUpdated", "GroupUpdated", "GroupUpdatedCodec"]
