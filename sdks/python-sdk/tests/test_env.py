import os

from xmtp.env import load_client_options_from_env
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
