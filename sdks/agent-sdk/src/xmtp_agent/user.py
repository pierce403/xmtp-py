"""User helpers for XMTP agents."""

from __future__ import annotations

from dataclasses import dataclass

from eth_account import Account
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.signers import EoaSigner
from xmtp.signers import create_signer as _create_signer
from xmtp.utils import is_hex_string


@dataclass(slots=True)
class User:
    """User wallet wrapper."""

    private_key: str
    address: str


def _normalize_key(private_key: str) -> str:
    if not is_hex_string(private_key):
        raise ValueError("Private key must be a hex string")
    if not private_key.startswith("0x"):
        return f"0x{private_key}"
    return private_key


def create_user(private_key: str | None = None) -> User:
    """Create a user from an optional private key."""

    if private_key is None:
        account = Account.create()
        key_hex = account.key.hex()
        key_hex = f"0x{key_hex}"
        return User(private_key=key_hex, address=account.address)

    key = _normalize_key(private_key)
    account = Account.from_key(key)
    return User(private_key=key, address=account.address)


def create_signer(user_or_key: User | str) -> EoaSigner:
    """Create an EOA signer from a user or private key."""

    key = user_or_key.private_key if isinstance(user_or_key, User) else user_or_key
    return _create_signer(_normalize_key(key))


def create_identifier(user: User) -> Identifier:
    """Create an XMTP identifier for a user."""

    return Identifier(kind=IdentifierKind.ETHEREUM, value=user.address.lower())


__all__ = ["User", "create_user", "create_signer", "create_identifier"]
