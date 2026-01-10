from __future__ import annotations

import types
from enum import Enum

import pytest


class FfiConsentState(str, Enum):
    ALLOWED = 'allowed'
    DENIED = 'denied'
    UNKNOWN = 'unknown'


class FfiSubscribeError(Exception):
    pass


class _Bindings(types.SimpleNamespace):
    pass


@pytest.fixture()
def fake_bindings(monkeypatch: pytest.MonkeyPatch):
    bindings = _Bindings(
        FfiConsentState=FfiConsentState,
        FfiSubscribeError=FfiSubscribeError,
    )

    import xmtp.bindings
    import xmtp_agent.agent
    import xmtp_agent.context

    for module in (xmtp.bindings, xmtp_agent.agent, xmtp_agent.context):
        monkeypatch.setattr(module, 'NativeBindings', bindings, raising=False)

    return bindings
