"""Read receipt content type for XMTP."""

from __future__ import annotations

from typing import Protocol, TypeAlias, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _FfiReadReceipt(Protocol):
    def __init__(self) -> None: ...


class _Bindings(Protocol):
    FfiReadReceipt: type[_FfiReadReceipt]

    def encode_read_receipt(self, payload: _FfiReadReceipt) -> bytes: ...

    def decode_read_receipt(self, data: bytes) -> object: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeReadReceipt = ContentTypeId(
    authority_id="xmtp.org",
    type_id="readReceipt",
    version_major=1,
    version_minor=0,
)


ReadReceipt: TypeAlias = dict[str, object]


class ReadReceiptCodec(ContentCodec[ReadReceipt]):
    """Codec for read receipt messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeReadReceipt

    def encode(self, content: ReadReceipt, registry: CodecRegistry | None = None) -> EncodedContent:
        encoded = _bindings().encode_read_receipt(_bindings().FfiReadReceipt())
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> ReadReceipt:
        _bindings().decode_read_receipt(content.content)
        return {}

    def fallback(self, content: ReadReceipt) -> str | None:
        return None

    def should_push(self, content: ReadReceipt) -> bool:
        return False


__all__ = ["ContentTypeReadReceipt", "ReadReceipt", "ReadReceiptCodec"]
