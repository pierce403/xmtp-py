"""Content type primitives for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

TContent = TypeVar("TContent")


@dataclass(frozen=True, slots=True)
class ContentTypeId:
    """Content type identifier."""

    authority_id: str
    type_id: str
    version_major: int
    version_minor: int

    def __str__(self) -> str:
        return f"{self.authority_id}/{self.type_id}:{self.version_major}.{self.version_minor}"

    def same_as(self, other: ContentTypeId) -> bool:
        return (
            self.authority_id == other.authority_id
            and self.type_id == other.type_id
            and self.version_major == other.version_major
            and self.version_minor == other.version_minor
        )


@dataclass(slots=True)
class EncodedContent:
    """Encoded content payload."""

    type_id: ContentTypeId
    parameters: dict[str, str]
    content: bytes
    fallback: str | None = None
    compression: int | None = None


class CodecRegistry(Protocol):
    """Registry for content codecs."""

    def codec_for(self, content_type: ContentTypeId) -> ContentCodec[Any] | None: ...


class ContentCodec(Protocol[TContent]):
    """Protocol for content codecs."""

    @property
    def content_type(self) -> ContentTypeId: ...

    def encode(
        self, content: TContent, registry: CodecRegistry | None = None
    ) -> EncodedContent: ...

    def decode(
        self, content: EncodedContent, registry: CodecRegistry | None = None
    ) -> TContent: ...

    def fallback(self, content: TContent) -> str | None: ...

    def should_push(self, content: TContent) -> bool: ...


class BaseContentCodec(Generic[TContent]):
    """Base class for content codecs with default behaviors."""

    @property
    def content_type(self) -> ContentTypeId:
        raise NotImplementedError

    def encode(self, content: TContent, registry: CodecRegistry | None = None) -> EncodedContent:
        raise NotImplementedError

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> TContent:
        raise NotImplementedError

    def fallback(self, content: TContent) -> str | None:
        return None

    def should_push(self, content: TContent) -> bool:
        return True


def content_types_are_equal(a: ContentTypeId, b: ContentTypeId) -> bool:
    """Return True if content type IDs are equal."""

    return a.same_as(b)


def content_type_to_string(content_type: ContentTypeId) -> str:
    """Convert content type ID to string form."""

    return str(content_type)


def content_type_from_string(content_type_string: str) -> ContentTypeId:
    """Parse content type ID from string form."""
    import re

    match = re.match(r"^([^/]+)/([^:]+):(\d+)\.(\d+)$", content_type_string)
    if not match:
        raise ValueError(
            f'Invalid content type string: "{content_type_string}". '
            'Expected format: "authorityId/typeId:majorVersion.minorVersion"'
        )
    authority_id, type_id, major_str, minor_str = match.groups()
    return ContentTypeId(
        authority_id=authority_id,
        type_id=type_id,
        version_major=int(major_str),
        version_minor=int(minor_str),
    )


__all__ = [
    "BaseContentCodec",
    "CodecRegistry",
    "ContentCodec",
    "ContentTypeId",
    "EncodedContent",
    "content_type_from_string",
    "content_type_to_string",
    "content_types_are_equal",
]
