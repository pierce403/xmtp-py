"""Bindings loader for libxmtp (UniFFI)."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from xmtp_bindings import xmtpv3
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        'xmtp-bindings is required. Build bindings/python or install the package.'
    ) from exc

if TYPE_CHECKING:  # pragma: no cover - typing only
    from types import ModuleType

NativeBindings = xmtpv3
