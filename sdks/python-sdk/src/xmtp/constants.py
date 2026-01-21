"""XMTP network constants."""

from __future__ import annotations

from typing import Final

API_URLS: Final[dict[str, str]] = {
    "local": "http://localhost:5556",
    "dev": "https://grpc.dev.xmtp.network:443",
    "production": "https://grpc.production.xmtp.network:443",
}

HISTORY_SYNC_URLS: Final[dict[str, str]] = {
    "local": "http://localhost:5558",
    "dev": "https://message-history.dev.ephemera.network",
    "production": "https://message-history.production.ephemera.network",
}
