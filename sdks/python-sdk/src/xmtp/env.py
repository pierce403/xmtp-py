"""Environment variable helpers for XMTP."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import cast

from xmtp.signers import Signer, create_signer
from xmtp.types import ClientOptions, LogLevel, XmtpEnv
from xmtp.utils import is_hex_string


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def _parse_log_level(value: str | None) -> LogLevel | None:
    if value is None:
        return None
    try:
        return LogLevel(value)
    except ValueError:
        return None


def load_client_options_from_env(options: ClientOptions | None = None) -> ClientOptions:
    """Load client options overrides from environment variables."""

    base = options or ClientOptions()
    updated = replace(base)

    env_value = os.getenv("XMTP_ENV")
    if env_value in {"local", "dev", "production"}:
        updated.env = cast(XmtpEnv, env_value)

    api_url = os.getenv("XMTP_API_URL")
    if api_url:
        updated.api_url = api_url

    history_sync_url = os.getenv("XMTP_HISTORY_SYNC_URL")
    if history_sync_url is not None:
        normalized = history_sync_url.strip().lower()
        if normalized in {"", "none", "disable", "disabled", "off"}:
            updated.disable_history_sync = True
            updated.history_sync_url = None
        else:
            updated.history_sync_url = history_sync_url

    gateway_host = os.getenv("XMTP_GATEWAY_HOST")
    if gateway_host:
        updated.gateway_host = gateway_host

    db_encryption_key = os.getenv("XMTP_DB_ENCRYPTION_KEY")
    if db_encryption_key:
        updated.db_encryption_key = db_encryption_key

    db_directory = os.getenv("XMTP_DB_DIRECTORY")
    if db_directory:
        os.makedirs(db_directory, exist_ok=True, mode=0o700)

        def db_path(inbox_id: str) -> str:
            path = os.path.join(db_directory, f"xmtp-{inbox_id}.db3")
            print(f'Saving local database to "{path}"')
            return path

        updated.db_path = db_path

    if _is_truthy(os.getenv("XMTP_FORCE_DEBUG")):
        updated.debug_events_enabled = True
        updated.structured_logging = True
        level = _parse_log_level(os.getenv("XMTP_FORCE_DEBUG_LEVEL"))
        updated.logging_level = level or LogLevel.WARN

    if _is_truthy(os.getenv("XMTP_DISABLE_HISTORY_SYNC")):
        updated.disable_history_sync = True
        updated.history_sync_url = None

    return updated


def load_signer_from_env() -> Signer:
    """Create an EOA signer from XMTP_WALLET_KEY."""

    wallet_key = os.getenv("XMTP_WALLET_KEY")
    if wallet_key is None:
        raise ValueError("XMTP_WALLET_KEY is not set")
    if not is_hex_string(wallet_key):
        raise ValueError("XMTP_WALLET_KEY must be a hex string")
    if not wallet_key.startswith("0x"):
        wallet_key = f"0x{wallet_key}"
    return create_signer(wallet_key)


__all__ = ["load_client_options_from_env", "load_signer_from_env"]
