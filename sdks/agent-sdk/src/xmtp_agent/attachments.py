"""Attachment utilities for agents."""

from __future__ import annotations

import asyncio
import hashlib
from typing import cast
from urllib.request import Request, urlopen

from xmtp_content_type_remote_attachment import RemoteAttachment


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def download_remote_attachment(remote_attachment: RemoteAttachment) -> bytes:
    """Download a remote attachment and verify its digest."""

    def fetch() -> bytes:
        request = Request(remote_attachment.url, method="GET")
        with urlopen(request, timeout=30) as response:
            if response.status >= 400:
                raise ValueError(
                    f"Unable to fetch remote attachment: {response.status} {response.reason}"
                )
            return cast(bytes, response.read())

    payload = cast(bytes, await asyncio.to_thread(fetch))
    digest = _sha256_hex(payload)
    if digest.lower() != remote_attachment.content_digest.lower():
        raise ValueError("Remote attachment digest does not match payload")
    return payload


__all__ = ["download_remote_attachment"]
