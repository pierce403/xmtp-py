import os

import pytest

from xmtp.env import _is_truthy, _parse_log_level, load_client_options_from_env, load_signer_from_env
from xmtp.types import ClientOptions, LogLevel


def test_load_client_options_from_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('XMTP_ENV', 'production')
    monkeypatch.setenv('XMTP_DB_ENCRYPTION_KEY', '0xdeadbeef')
    monkeypatch.setenv('XMTP_DB_DIRECTORY', str(tmp_path))
    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'debug')

    options = load_client_options_from_env(ClientOptions())

    assert options.env == 'production'
    assert options.db_encryption_key == '0xdeadbeef'
    assert options.debug_events_enabled is True
    assert options.structured_logging is True
    assert options.logging_level == LogLevel.DEBUG
    assert options.db_path is not None

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


def test_load_client_options_invalid_env(monkeypatch) -> None:
    monkeypatch.setenv('XMTP_ENV', 'invalid')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.env == 'dev'


def test_load_client_options_invalid_debug_level(monkeypatch) -> None:
    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'invalid')
    options = load_client_options_from_env(ClientOptions(env='dev'))
    assert options.logging_level == LogLevel.WARN


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

    monkeypatch.setenv('XMTP_WALLET_KEY', '1' * 64)
    signer = load_signer_from_env()
    assert signer is not None
