"""Bindings loader for libxmtp (UniFFI)."""

from __future__ import annotations

class _MissingBindings:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def __getattr__(self, name: str) -> object:
        raise ImportError(
            'xmtp-bindings is required. Build bindings/python or install the package.'
        ) from self._error


try:
    from xmtp_bindings import xmtpv3
except (ImportError, OSError) as exc:  # pragma: no cover - import guard
    NativeBindings = _MissingBindings(exc)
else:
    NativeBindings = xmtpv3
