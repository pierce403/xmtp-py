"""Identifier types for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IdentifierKind(str, Enum):
    """Supported identifier kinds."""

    ETHEREUM = "ethereum"
    PASSKEY = "passkey"


@dataclass(frozen=True, slots=True)
class Identifier:
    """Identifier for XMTP inbox lookups."""

    kind: IdentifierKind
    value: str
