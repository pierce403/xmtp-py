"""Markdown content type for XMTP."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _Bindings(Protocol):
    def encode_markdown(self, text: str) -> bytes: ...

    def decode_markdown(self, data: bytes) -> str: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return xmtpv3  # pragma: no cover - requires native bindings


ContentTypeMarkdown = ContentTypeId(
    authority_id="xmtp.org",
    type_id="markdown",
    version_major=1,
    version_minor=0,
)


class Encoding(str, Enum):
    UTF8 = "UTF-8"
    UNKNOWN = "unknown"


class MarkdownCodec(ContentCodec[str]):
    """Codec for markdown messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeMarkdown

    def encode(self, content: str, registry: CodecRegistry | None = None) -> EncodedContent:
        encoded = _bindings().encode_markdown(content)
        return EncodedContent(
            type_id=self.content_type,
            parameters={"encoding": Encoding.UTF8.value},
            content=encoded,
        )

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> str:
        encoding = content.parameters.get("encoding")
        if encoding is None:
            raise ValueError("Missing encoding for markdown content")
        if encoding.upper() != Encoding.UTF8.value:
            raise ValueError(f"unrecognized encoding {encoding}")
        if not isinstance(content.content, (bytes, bytearray)):
            raise TypeError("Markdown content payload must be bytes")
        return _bindings().decode_markdown(bytes(content.content))

    def fallback(self, content: str) -> str | None:
        return None

    def should_push(self, content: str) -> bool:
        return True


__all__ = ["ContentTypeMarkdown", "Encoding", "MarkdownCodec"]
