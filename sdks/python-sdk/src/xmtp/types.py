"""Shared XMTP type definitions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from xmtp_content_type_primitives import ContentCodec

from xmtp.constants import API_URLS, HISTORY_SYNC_URLS

XmtpEnv = Literal["local", "dev", "production"]


class LogLevel(str, Enum):
    """Logging levels for libxmtp."""

    OFF = "off"
    ERROR = "error"
    WARN = "warn"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"


@dataclass(slots=True)
class ClientOptions:
    """Options for constructing an XMTP client.

    Attributes:
        env: Network environment to target.
        api_url: Optional override for the XMTP API URL.
        history_sync_url: Optional override for history sync URL.
        disable_history_sync: Disable history sync and use the primary API for identity calls.
            Defaults to True.
        gateway_host: Optional gateway host for d14n.
        db_path: Optional database path (string, None, or function).
        db_encryption_key: Optional database encryption key bytes or hex string.
        structured_logging: Enable structured JSON logging.
        logging_level: Logging level for libxmtp.
        rust_log: Override RUST_LOG for native bindings (defaults to "off" if unset).
        disable_auto_register: Skip automatic registration.
        disable_device_sync: Disable device sync worker.
        app_version: Optional app version string to pass to the backend.
        debug_events_enabled: Enable debug events tracking.
        nonce: Nonce for generating inbox IDs when needed.
        codecs: Optional content codecs to register.
    """

    env: XmtpEnv = "dev"
    api_url: str | None = None
    history_sync_url: str | None = None
    disable_history_sync: bool = True
    gateway_host: str | None = None
    db_path: str | None | Literal["auto"] | Callable[[str], str] = "auto"
    db_encryption_key: bytes | str | None = None
    structured_logging: bool = False
    logging_level: LogLevel | None = None
    rust_log: str | None = None
    disable_auto_register: bool = False
    disable_device_sync: bool = False
    app_version: str | None = None
    debug_events_enabled: bool = False
    nonce: int | None = None
    codecs: Sequence[ContentCodec[object]] | None = None

    def resolved_api_url(self) -> str:
        """Return the API URL based on env and overrides."""

        if self.api_url:
            return self.api_url
        return API_URLS[self.env]

    def resolved_history_sync_url(self) -> str | None:
        """Return the history sync URL based on env and overrides."""

        if self.disable_history_sync:
            return None
        if self.history_sync_url is not None:
            return self.history_sync_url
        return HISTORY_SYNC_URLS[self.env]
