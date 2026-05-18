"""Bindings loader for libxmtp (UniFFI)."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from importlib import metadata
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypeVar, cast

from xmtp.errors import BindingCompatibilityError

if TYPE_CHECKING:
    from xmtp_bindings import xmtpv3 as NativeBindings

_T = TypeVar("_T")

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


def get_optional_binding_symbol(name: str, default: _T) -> object | _T:
    """Return an optional native binding symbol without hard-failing on drift."""

    try:
        return cast(object | _T, getattr(NativeBindings, name))
    except (AttributeError, ImportError):
        return default


def get_bindings_version() -> str | None:
    """Return the installed xmtp-bindings version if it can be discovered."""

    try:
        import xmtp_bindings
    except ImportError:
        return None

    version = getattr(xmtp_bindings, "__version__", None)
    if isinstance(version, str):
        return version
    try:
        return metadata.version("xmtp-bindings")
    except metadata.PackageNotFoundError:
        return None


def get_native_stream_error_types() -> tuple[type[BaseException], ...]:
    """Return native stream error classes that exist in the loaded bindings."""

    error_types: list[type[BaseException]] = []
    for name in ("FfiSubscribeError", "FfiError", "InternalError"):
        symbol = get_optional_binding_symbol(name, None)
        if (
            isinstance(symbol, type)
            and issubclass(symbol, BaseException)
            and symbol is not BaseException
            and symbol is not Exception
        ):
            error_types.append(symbol)
    return tuple(error_types)


def _positional_parameter_count(symbol: object) -> int | None:
    try:
        signature = inspect.signature(cast(Callable[..., object], symbol))
    except (TypeError, ValueError):
        return None
    count = 0
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            return None
        if parameter.kind in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }:
            count += 1
    return count


def _require_symbols(module: ModuleType | object) -> None:
    missing = [
        name
        for name in (
            "connect_to_backend",
            "create_client",
            "get_inbox_id_for_identifier",
            "generate_inbox_id",
            "FfiIdentifier",
            "FfiIdentifierKind",
        )
        if not hasattr(module, name)
    ]
    if missing:
        raise BindingCompatibilityError(f"Missing required symbols: {', '.join(missing)}.")
    if not (hasattr(module, "FfiSyncWorkerMode") or hasattr(module, "FfiDeviceSyncMode")):
        raise BindingCompatibilityError(
            "Missing device sync mode enum (expected FfiSyncWorkerMode or FfiDeviceSyncMode)."
        )


def _validate_signature(module: ModuleType | object, name: str, supported_counts: set[int]) -> None:
    symbol = getattr(module, name)
    count = _positional_parameter_count(symbol)
    if count is not None and count not in supported_counts:
        expected = " or ".join(str(value) for value in sorted(supported_counts))
        raise BindingCompatibilityError(f"{name} accepts {count} args; expected {expected}.")


def check_binding_compatibility(
    expected_xmtp_version: str | None = None,
    module: ModuleType | object | None = None,
) -> None:
    """Validate the loaded binding surface before using native APIs."""

    bindings = NativeBindings if module is None else module
    try:
        _require_symbols(bindings)
        _validate_signature(bindings, "connect_to_backend", {6, 7})
        _validate_signature(bindings, "create_client", {10, 12})
    except ImportError as exc:
        raise BindingCompatibilityError(str(exc)) from exc

    create_count = _positional_parameter_count(cast(Any, bindings).create_client)
    if create_count == 10 and not (
        hasattr(bindings, "DbOptions") or hasattr(bindings, "FfiDbOptions")
    ):
        raise BindingCompatibilityError(
            "create_client uses DbOptions, but no DbOptions/FfiDbOptions class is exported."
        )

    bindings_version = get_bindings_version()
    if expected_xmtp_version and bindings_version and bindings_version != expected_xmtp_version:
        raise BindingCompatibilityError(
            f"xmtp version {expected_xmtp_version} requires xmtp-bindings "
            f"{expected_xmtp_version}, but {bindings_version} is installed."
        )


__all__ = [
    "NativeBindings",
    "check_binding_compatibility",
    "get_bindings_version",
    "get_native_stream_error_types",
    "get_optional_binding_symbol",
]
