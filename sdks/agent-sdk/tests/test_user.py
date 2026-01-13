import pytest

from xmtp.identifiers import IdentifierKind
from xmtp_agent.user import create_identifier, create_signer, create_user


def test_create_user_random() -> None:
    user = create_user()
    assert user.private_key.startswith('0x')
    assert user.address.startswith('0x')


def test_create_user_with_key() -> None:
    key = '0x' + '1' * 64
    user = create_user(key)
    assert user.private_key == key


def test_create_user_with_key_no_prefix() -> None:
    key = '1' * 64
    user = create_user(key)
    assert user.private_key == '0x' + key


def test_create_signer_from_user() -> None:
    user = create_user('0x' + '2' * 64)
    signer = create_signer(user)
    assert signer is not None


def test_create_signer_from_key_normalizes() -> None:
    signer = create_signer('3' * 64)
    assert signer is not None


def test_create_identifier_lowercases() -> None:
    user = create_user('0x' + 'a' * 64)
    identifier = create_identifier(user)
    assert identifier.kind is IdentifierKind.ETHEREUM
    assert identifier.value == user.address.lower()


def test_create_user_invalid_key() -> None:
    with pytest.raises(ValueError, match='Private key must be a hex string'):
        create_user('invalid')
