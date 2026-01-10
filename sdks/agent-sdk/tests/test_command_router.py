import pytest

from xmtp_agent.command_router import CommandRouter
from .helpers import DummyContext


@pytest.mark.asyncio
async def test_command_router_handles_command() -> None:
    router = CommandRouter()
    handled = False

    async def handler(ctx) -> None:
        nonlocal handled
        handled = True
        assert ctx.message.content == 'arg1 arg2'

    router.command('/ping', handler)

    ctx = DummyContext('/ping arg1 arg2')
    result = await router.handle(ctx)

    assert result is True
    assert handled is True


@pytest.mark.asyncio
async def test_command_router_default_handler() -> None:
    router = CommandRouter()
    handled = False

    async def default_handler(ctx) -> None:
        nonlocal handled
        handled = True

    router.default(default_handler)

    ctx = DummyContext('hello')
    result = await router.handle(ctx)

    assert result is True
    assert handled is True
