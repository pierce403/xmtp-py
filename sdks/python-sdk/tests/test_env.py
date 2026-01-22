import os

import pytest

from xmtp.env import (
    _is_truthy,
    _parse_log_level,
    apply_rust_log_from_options,
    load_client_options_from_env,
    load_signer_from_env,
)
from xmtp.types import ClientOptions, LogLevel


def test_load_client_options_from_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('XMTP_ENV', 'production')
    monkeypatch.setenv('XMTP_API_URL', 'https://api.example')
    monkeypatch.setenv('XMTP_HISTORY_SYNC_URL', 'https://history.example')
    monkeypatch.setenv('XMTP_GATEWAY_HOST', 'gateway.example')
    monkeypatch.setenv('XMTP_DB_ENCRYPTION_KEY', '0xdeadbeef')
    monkeypatch.setenv('XMTP_DB_DIRECTORY', str(tmp_path))
    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'debug')
    monkeypatch.setenv('XMTP_RUST_LOG', 'warn')

    options = load_client_options_from_env(ClientOptions())

    assert options.env == 'production'
    assert options.api_url == 'https://api.example'
    assert options.history_sync_url == 'https://history.example'
    assert options.disable_history_sync is False
    assert options.gateway_host == 'gateway.example'
    assert options.db_encryption_key == '0xdeadbeef'
    assert options.debug_events_enabled is True
    assert options.structured_logging is True
    assert options.logging_level == LogLevel.DEBUG
    assert options.db_path is not None
    assert options.rust_log == 'warn'

    db_path = options.db_path('inbox') if callable(options.db_path) else options.db_path
    assert db_path is not None
    assert os.path.basename(db_path) == 'xmtp-inbox.db3'


def test_load_client_options_from_env_defaults(monkeypatch) -> None:
    monkeypatch.delenv('XMTP_ENV', raising=False)
    monkeypatch.delenv('XMTP_FORCE_DEBUG', raising=False)
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.env == 'dev'
    assert options.structured_logging is False
    assert options.debug_events_enabled is False
    assert options.disable_history_sync is True
    assert options.rust_log is None


def test_load_client_options_invalid_env(monkeypatch) -> None:
    monkeypatch.setenv('XMTP_ENV', 'invalid')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.env == 'dev'


def test_load_client_options_invalid_debug_level(monkeypatch) -> None:
    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'invalid')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.logging_level == LogLevel.WARN


def test_load_client_options_disable_history_sync(monkeypatch) -> None:
    monkeypatch.setenv('XMTP_HISTORY_SYNC_URL', 'disabled')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.disable_history_sync is True
    assert options.resolved_history_sync_url() is None

    monkeypatch.setenv('XMTP_HISTORY_SYNC_URL', 'https://history.example')
    monkeypatch.setenv('XMTP_DISABLE_HISTORY_SYNC', '1')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.disable_history_sync is True
    assert options.history_sync_url is None


def test_is_truthy() -> None:
    assert _is_truthy('1') is True
    assert _is_truthy('true') is True
    assert _is_truthy('yes') is True
    assert _is_truthy('0') is False
    assert _is_truthy('false') is False
    assert _is_truthy('') is False
    assert _is_truthy(None) is False


def test_parse_log_level() -> None:
    assert _parse_log_level('debug') == LogLevel.DEBUG
    assert _parse_log_level('bad') is None
    assert _parse_log_level(None) is None


def test_load_signer_from_env(monkeypatch) -> None:
    monkeypatch.delenv('XMTP_WALLET_KEY', raising=False)
    with pytest.raises(ValueError, match='XMTP_WALLET_KEY is not set'):
        load_signer_from_env()

    monkeypatch.setenv('XMTP_WALLET_KEY', 'not-hex')
    with pytest.raises(ValueError, match='XMTP_WALLET_KEY must be a hex string'):
        load_signer_from_env()

    monkeypatch.setenv('XMTP_WALLET_KEY', '0x' + '1' * 64)
    signer = load_signer_from_env()
    assert signer is not None


def test_apply_rust_log_from_options(monkeypatch) -> None:
    monkeypatch.delenv('RUST_LOG', raising=False)
    apply_rust_log_from_options(ClientOptions(env='dev'))
    assert os.environ['RUST_LOG'] == 'off'

    monkeypatch.setenv('RUST_LOG', 'info')
    apply_rust_log_from_options(ClientOptions(env='dev'))
    assert os.environ['RUST_LOG'] == 'info'

    apply_rust_log_from_options(ClientOptions(env='dev', rust_log='error'))
    assert os.environ['RUST_LOG'] == 'error'

    monkeypatch.setenv('XMTP_WALLET_KEY', '1' * 64)
    signer = load_signer_from_env()
    assert signer is not None
