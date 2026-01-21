"""Attachment content types for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


def _bindings() -> Any:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return xmtpv3  # pragma: no cover - requires native bindings


ContentTypeAttachment = ContentTypeId(
    authority_id="xmtp.org",
    type_id="attachment",
    version_major=1,
    version_minor=0,
)

ContentTypeRemoteAttachment = ContentTypeId(
    authority_id="xmtp.org",
    type_id="remoteStaticAttachment",
    version_major=1,
    version_minor=0,
)


@dataclass(slots=True)
class Attachment:
    """Attachment payload."""

    filename: str | None
    mime_type: str
    data: bytes


@dataclass(slots=True)
class RemoteAttachment:
    """Remote attachment metadata."""

    url: str
    content_digest: str
    salt: bytes
    nonce: bytes
    secret: bytes
    scheme: str
    content_length: int
    filename: str | None


class AttachmentCodec(ContentCodec[Attachment]):
    """Codec for attachment payloads."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeAttachment

    def encode(self, content: Attachment, registry: CodecRegistry | None = None) -> EncodedContent:
        attachment = _bindings().FfiAttachment(
            filename=content.filename,
            mime_type=content.mime_type,
            content=content.data,
        )
        encoded = _bindings().encode_attachment(attachment)
        parameters = {"mimeType": content.mime_type}
        if content.filename:
            parameters["filename"] = content.filename
        return EncodedContent(type_id=self.content_type, parameters=parameters, content=encoded)

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> Attachment:
        decoded = _bindings().decode_attachment(content.content)
        return Attachment(
            filename=decoded.filename,
            mime_type=decoded.mime_type,
            data=decoded.content,
        )

    def fallback(self, content: Attachment) -> str | None:
        filename = content.filename or "attachment"
        return f"Can't display \"{filename}\". This app doesn't support attachments."

    def should_push(self, content: Attachment) -> bool:
        return True


class RemoteAttachmentCodec(ContentCodec[RemoteAttachment]):
    """Codec for remote attachment metadata."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeRemoteAttachment

    def encode(
        self, content: RemoteAttachment, registry: CodecRegistry | None = None
    ) -> EncodedContent:
        parsed = urlparse(content.url)
        if parsed.scheme.lower() != "https":
            raise ValueError("Remote attachment URL must use https scheme")
        remote_attachment = _bindings().FfiRemoteAttachment(
            url=content.url,
            content_digest=content.content_digest,
            secret=content.secret,
            salt=content.salt,
            nonce=content.nonce,
            scheme=content.scheme,
            content_length=content.content_length,
            filename=content.filename,
        )
        encoded = _bindings().encode_remote_attachment(remote_attachment)
        parameters = {
            "contentDigest": content.content_digest,
            "salt": content.salt.hex(),
            "nonce": content.nonce.hex(),
            "secret": content.secret.hex(),
            "scheme": content.scheme,
            "contentLength": str(content.content_length),
        }
        if content.filename:
            parameters["filename"] = content.filename
        return EncodedContent(type_id=self.content_type, parameters=parameters, content=encoded)

    def decode(
        self, content: EncodedContent, registry: CodecRegistry | None = None
    ) -> RemoteAttachment:
        decoded = _bindings().decode_remote_attachment(content.content)
        return RemoteAttachment(
            url=decoded.url,
            content_digest=decoded.content_digest,
            secret=decoded.secret,
            salt=decoded.salt,
            nonce=decoded.nonce,
            scheme=decoded.scheme,
            content_length=decoded.content_length,
            filename=decoded.filename,
        )

    def fallback(self, content: RemoteAttachment) -> str | None:
        filename = content.filename or "attachment"
        return f"Can't display \"{filename}\". This app doesn't support attachments."

    def should_push(self, content: RemoteAttachment) -> bool:
        return True


__all__ = [
    "Attachment",
    "AttachmentCodec",
    "ContentTypeAttachment",
    "ContentTypeRemoteAttachment",
    "RemoteAttachment",
    "RemoteAttachmentCodec",
]
