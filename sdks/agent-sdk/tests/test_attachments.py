import asyncio
import hashlib

import pytest

from xmtp_agent.attachments import download_remote_attachment
from xmtp_content_type_remote_attachment import RemoteAttachment


class _Response:
    def __init__(self, status: int, data: bytes) -> None:
        self.status = status
        self.reason = 'OK' if status < 400 else 'Bad'
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.asyncio
async def test_download_remote_attachment_ok(monkeypatch) -> None:
    payload = b'hello'
    attachment = RemoteAttachment(
        url='https://example',
        content_digest=_digest(payload),
        salt=b'salt',
        nonce=b'nonce',
        secret=b'secret',
        scheme='https',
        content_length=len(payload),
        filename='file.txt',
    )

    def fake_urlopen(request, timeout=30):
        return _Response(200, payload)

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.attachments.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    data = await download_remote_attachment(attachment)
    assert data == payload


@pytest.mark.asyncio
async def test_download_remote_attachment_http_error(monkeypatch) -> None:
    attachment = RemoteAttachment(
        url='https://example',
        content_digest='digest',
        salt=b'salt',
        nonce=b'nonce',
        secret=b'secret',
        scheme='https',
        content_length=1,
        filename=None,
    )

    def fake_urlopen(request, timeout=30):
        return _Response(500, b'')

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.attachments.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    with pytest.raises(ValueError, match='Unable to fetch remote attachment'):
        await download_remote_attachment(attachment)


@pytest.mark.asyncio
async def test_download_remote_attachment_digest_mismatch(monkeypatch) -> None:
    payload = b'hello'
    attachment = RemoteAttachment(
        url='https://example',
        content_digest='wrong',
        salt=b'salt',
        nonce=b'nonce',
        secret=b'secret',
        scheme='https',
        content_length=len(payload),
        filename=None,
    )

    def fake_urlopen(request, timeout=30):
        return _Response(200, payload)

    async def fake_to_thread(fn):
        return fn()

    monkeypatch.setattr('xmtp_agent.attachments.urlopen', fake_urlopen)
    monkeypatch.setattr(asyncio, 'to_thread', fake_to_thread)

    with pytest.raises(ValueError, match='digest does not match'):
        await download_remote_attachment(attachment)
