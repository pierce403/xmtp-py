"""Read receipt content type for XMTP."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings


def _bindings() -> xmtpv3:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return xmtpv3  # pragma: no cover - requires native bindings


ContentTypeReadReceipt = ContentTypeId(
    authority_id="xmtp.org",
    type_id="readReceipt",
    version_major=1,
    version_minor=0,
)


class ReadReceiptCodec(ContentCodec[dict]):
    """Codec for read receipt messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeReadReceipt

    def encode(self, content: dict, registry: CodecRegistry | None = None) -> EncodedContent:
        encoded = _bindings().encode_read_receipt(_bindings().FfiReadReceipt())
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> dict:
        _bindings().decode_read_receipt(content.content)
        return {}

    def fallback(self, content: dict) -> str | None:
        return None

    def should_push(self, content: dict) -> bool:
        return False


__all__ = ["ContentTypeReadReceipt", "ReadReceiptCodec"]
