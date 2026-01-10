from xmtp.utils import coerce_db_encryption_key, hex_to_bytes, is_hex_string


def test_is_hex_string() -> None:
    assert is_hex_string('0xabc123')
    assert is_hex_string('abc123')
    assert not is_hex_string('0xabc123g')
    assert is_hex_string('0x' + 'a' * 64, length=64)
    assert not is_hex_string('0x' + 'a' * 63, length=64)


def test_hex_to_bytes() -> None:
    assert hex_to_bytes('0x0a0b') == b'\x0a\x0b'
    assert hex_to_bytes('0a0b') == b'\x0a\x0b'


def test_coerce_db_encryption_key() -> None:
    assert coerce_db_encryption_key(b'abc') == b'abc'
    assert coerce_db_encryption_key('0x0a0b') == b'\x0a\x0b'
