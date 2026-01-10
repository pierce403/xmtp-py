import pytest

pytest.importorskip('xmtp_bindings')

from xmtp import Client
from xmtp_content_type_text import ContentTypeText


def test_client_registers_default_codecs() -> None:
    client = Client()
    assert client.codec_for(ContentTypeText) is not None
    assert client.account_identifier is None
