"""Text content type for XMTP."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3


def _bindings() -> "xmtpv3":
    from xmtp_bindings import xmtpv3

    return xmtpv3


ContentTypeText = ContentTypeId(
    authority_id='xmtp.org',
    type_id='text',
    version_major=1,
    version_minor=0,
)


class Encoding(str, Enum):
    UTF8 = 'UTF-8'
    UNKNOWN = 'unknown'


class TextCodec(ContentCodec[str]):
    """Codec for plain text messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeText

    def encode(self, content: str, registry: CodecRegistry | None = None) -> EncodedContent:
        encoded = _bindings().encode_text(content)
        return EncodedContent(
            type_id=self.content_type,
            parameters={'encoding': Encoding.UTF8.value},
            content=encoded,
        )

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> str:
        encoding = content.parameters.get('encoding')
        if encoding is None:
            raise ValueError('Missing encoding for text content')
        if encoding.upper() != Encoding.UTF8.value:
            raise ValueError(f'unrecognized encoding {encoding}')
        if not isinstance(content.content, (bytes, bytearray)):
            raise TypeError('Text content payload must be bytes')
        return _bindings().decode_text(bytes(content.content))

    def fallback(self, content: str) -> str | None:
        return None

    def should_push(self, content: str) -> bool:
        return True


__all__ = ['ContentTypeText', 'Encoding', 'TextCodec']
