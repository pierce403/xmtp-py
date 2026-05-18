"""Python bindings for libxmtp generated via UniFFI."""

__version__ = "0.1.6"

try:
    from xmtp_bindings.xmtpv3 import *  # noqa: F403
except OSError as exc:  # pragma: no cover - native library missing
    raise ImportError(
        "libxmtpv3 native library is unavailable. Build libxmtp and copy libxmtpv3.so "
        "next to xmtpv3.py (see bindings/python/README.md)."
    ) from exc  # pragma: no cover

__all__ = ["__version__"]  # populated by wildcard import  # pragma: no cover
