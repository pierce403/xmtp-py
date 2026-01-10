"""Read receipt content type for XMTP."""

from __future__ import annotations

from xmtp_bindings import xmtpv3
from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


ContentTypeReadReceipt = ContentTypeId(
    authority_id='xmtp.org',
    type_id='readReceipt',
    version_major=1,
    version_minor=0,
)


class ReadReceiptCodec(ContentCodec[dict]):
    """Codec for read receipt messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeReadReceipt

    def encode(self, content: dict, registry: CodecRegistry | None = None) -> EncodedContent:
        encoded = xmtpv3.encode_read_receipt(xmtpv3.FfiReadReceipt())
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> dict:
        xmtpv3.decode_read_receipt(content.content)
        return {}

    def fallback(self, content: dict) -> str | None:
        return None

    def should_push(self, content: dict) -> bool:
        return False


__all__ = ['ContentTypeReadReceipt', 'ReadReceiptCodec']
