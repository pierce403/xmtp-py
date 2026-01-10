from xmtp.constants import API_URLS, HISTORY_SYNC_URLS
from xmtp.types import ClientOptions


def test_constants_have_expected_envs() -> None:
    assert set(API_URLS.keys()) == {'local', 'dev', 'production'}
    assert set(HISTORY_SYNC_URLS.keys()) == {'local', 'dev', 'production'}


def test_client_options_resolve_urls() -> None:
    options = ClientOptions(env='local')
    assert options.resolved_api_url() == API_URLS['local']
    assert options.resolved_history_sync_url() == HISTORY_SYNC_URLS['local']

    options.api_url = 'https://custom'
    options.history_sync_url = 'https://history'
    assert options.resolved_api_url() == 'https://custom'
    assert options.resolved_history_sync_url() == 'https://history'
