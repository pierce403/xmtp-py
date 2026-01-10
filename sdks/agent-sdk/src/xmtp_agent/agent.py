"""Agent class for XMTP."""

from __future__ import annotations

from collections.abc import Callable

from xmtp_agent.errors import AgentError
from xmtp_agent.middleware import ErrorMiddleware, Middleware


class Agent:
    """Main agent class with an event-driven API."""

    def __init__(self) -> None:
        self._middlewares: list[Middleware] = []
        self._error_middlewares: list[ErrorMiddleware] = []

    @classmethod
    async def create(
        cls,
        signer: object,
        options: object | None = None,
    ) -> Agent:
        """Create an agent with a signer."""

        raise AgentError('Agent.create not implemented')

    @classmethod
    async def create_from_env(cls) -> Agent:
        """Create an agent from environment variables."""

        raise AgentError('Agent.create_from_env not implemented')

    async def start(self) -> None:
        """Start the agent."""

        raise AgentError('Agent.start not implemented')

    async def stop(self) -> None:
        """Stop the agent."""

        raise AgentError('Agent.stop not implemented')

    def on(self, event: str, handler: Callable[..., object]) -> None:
        """Register an event handler."""

        raise AgentError('Agent.on not implemented')

    def use(self, middleware: Middleware) -> None:
        """Register middleware for message handling."""

        self._middlewares.append(middleware)

    @property
    def errors(self) -> Agent:
        """Return an object to register error middleware."""

        return self

    def use_error(self, middleware: ErrorMiddleware) -> None:
        """Register middleware for error handling."""

        self._error_middlewares.append(middleware)
