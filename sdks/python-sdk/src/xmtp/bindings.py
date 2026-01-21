"""Bindings loader for libxmtp (UniFFI)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3 as NativeBindings

try:
    from xmtp_bindings import xmtpv3 as _xmtpv3
except (ImportError, OSError) as exc:  # pragma: no cover - import guard

    class _MissingBindings:
        def __init__(self, error: Exception) -> None:
            self._error = error

        def __getattr__(self, name: str) -> object:
            raise ImportError(
                "xmtp-bindings is required. Build bindings/python or install the package."
            ) from self._error

    NativeBindings = _MissingBindings(exc)  # type: ignore[assignment]
else:
    NativeBindings = _xmtpv3

__all__ = ["NativeBindings"]
