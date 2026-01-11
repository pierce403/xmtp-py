import pytest

from xmtp_content_type_primitives import (
    BaseContentCodec,
    ContentTypeId,
    EncodedContent,
    content_type_from_string,
    content_type_to_string,
    content_types_are_equal,
)


def test_content_type_roundtrip() -> None:
    content_type = ContentTypeId(
        authority_id='xmtp.org',
        type_id='text',
        version_major=1,
        version_minor=0,
    )
    serialized = content_type_to_string(content_type)
    parsed = content_type_from_string(serialized)
    assert content_types_are_equal(content_type, parsed)
    assert str(content_type) == serialized


def test_base_content_codec_defaults() -> None:
    codec = BaseContentCodec()
    with pytest.raises(NotImplementedError):
        _ = codec.content_type
    with pytest.raises(NotImplementedError):
        codec.encode('hi')
    with pytest.raises(NotImplementedError):
        codec.decode(
            EncodedContent(
                type_id=ContentTypeId('xmtp.org', 'text', 1, 0),
                parameters={},
                content=b'',
            )
        )
    assert codec.fallback('hi') is None
    assert codec.should_push('hi') is True
