"""Utility helpers for XMTP."""

from __future__ import annotations

import re

_HEX_RE = re.compile(r"^(0x)?[0-9a-fA-F]+$")


def is_hex_string(value: str, length: int | None = None) -> bool:
    """Return True if value is a hex string.

    Args:
        value: String to validate.
        length: Optional length (in hex digits, excluding 0x).
    """

    if not _HEX_RE.match(value):
        return False

    normalized = value[2:] if value.startswith("0x") else value
    if length is None:
        return True
    return len(normalized) == length


def hex_to_bytes(value: str) -> bytes:
    """Convert a hex string (with or without 0x prefix) to bytes."""

    normalized = value[2:] if value.startswith("0x") else value
    return bytes.fromhex(normalized)


def coerce_db_encryption_key(value: bytes | str | None) -> bytes | None:
    """Normalize the database encryption key to bytes if provided."""

    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if is_hex_string(value):
        return hex_to_bytes(value)
    raise ValueError("db_encryption_key must be bytes or hex string")
