"""Shared XMTP type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

XmtpEnv = Literal['dev', 'production']


@dataclass(slots=True)
class ClientOptions:
    """Options for constructing an XMTP client.

    Attributes:
        env: Network environment to target.
        db_path: Optional database path.
        db_encryption_key: Optional database encryption key bytes.
        debug: Enable debug logging.
        debug_level: Optional debug log level.
    """

    env: XmtpEnv = 'dev'
    db_path: str | None = None
    db_encryption_key: bytes | None = None
    debug: bool = False
    debug_level: str | None = None
