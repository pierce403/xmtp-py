"""Context objects for agent handlers."""

from __future__ import annotations

from dataclasses import dataclass

from xmtp_agent.errors import AgentError


@dataclass(slots=True)
class MessageContext:
    """Context passed to message handlers."""

    async def send_text(self, text: str) -> None:
        """Send a text message."""

        raise AgentError('MessageContext.send_text not implemented')

    async def send_text_reply(self, text: str) -> None:
        """Send a text reply."""

        raise AgentError('MessageContext.send_text_reply not implemented')

    async def send_markdown(self, text: str) -> None:
        """Send a markdown message."""

        raise AgentError('MessageContext.send_markdown not implemented')

    async def send_reaction(self, reference: str, action: str) -> None:
        """Send a reaction to a message."""

        raise AgentError('MessageContext.send_reaction not implemented')


@dataclass(slots=True)
class ConversationContext:
    """Context passed to conversation handlers."""


@dataclass(slots=True)
class ClientContext:
    """Context passed to lifecycle handlers."""
