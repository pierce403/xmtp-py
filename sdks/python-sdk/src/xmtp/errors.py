"""Error types for XMTP."""

from __future__ import annotations


class XmtpError(Exception):
    """Base class for XMTP errors."""


class NotImplementedXmtpError(XmtpError):
    """Raised when a feature has not been implemented yet."""
