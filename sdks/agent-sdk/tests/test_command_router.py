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


def test_command_router_requires_slash() -> None:
    router = CommandRouter()
    with pytest.raises(ValueError, match='Command must start with'):
        router.command('ping', lambda ctx: None)


@pytest.mark.asyncio
async def test_command_router_command_list() -> None:
    router = CommandRouter()
    router.command('/HELP', lambda ctx: None)
    router.command('/Balance', lambda ctx: None)
    assert router.command_list == ['/help', '/balance']


@pytest.mark.asyncio
async def test_command_router_ignores_non_text() -> None:
    router = CommandRouter()

    class _Context:
        def __init__(self) -> None:
            self.message = DummyMessage('noop')

        def is_text(self) -> bool:
            return False

    ctx = _Context()
    result = await router.handle(ctx)
    assert result is False


@pytest.mark.asyncio
async def test_command_router_middleware_calls_next() -> None:
    router = CommandRouter()
    called = []

    async def next_handler() -> None:
        called.append('next')

    middleware = router.middleware()
    await middleware(DummyContext('hello'), next_handler)
    assert called == ['next']


@pytest.mark.asyncio
async def test_command_router_unhandled_command() -> None:
    router = CommandRouter()
    ctx = DummyContext('/unknown arg')
    assert await router.handle(ctx) is False


@pytest.mark.asyncio
async def test_command_router_empty_message() -> None:
    router = CommandRouter()
    ctx = DummyContext('')
    assert await router.handle(ctx) is False
