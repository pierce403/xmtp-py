from xmtp_content_type_primitives import (
    ContentTypeId,
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
