"""Bindings loader for libxmtp (UniFFI)."""

from __future__ import annotations

try:
    from xmtp_bindings import xmtpv3
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        'xmtp-bindings is required. Build bindings/python or install the package.'
    ) from exc

NativeBindings = xmtpv3
