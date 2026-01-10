"""Message filter helpers."""

from __future__ import annotations

from xmtp_agent.errors import AgentError


def is_text() -> bool:
    """Return True if the message is a text message."""

    raise AgentError('filters.is_text not implemented')


def is_reaction() -> bool:
    """Return True if the message is a reaction."""

    raise AgentError('filters.is_reaction not implemented')


def from_self() -> bool:
    """Return True if the message is from the agent itself."""

    raise AgentError('filters.from_self not implemented')


def has_content() -> bool:
    """Return True if the message has content."""

    raise AgentError('filters.has_content not implemented')
