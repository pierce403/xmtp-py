"""Agent SDK errors."""

from __future__ import annotations


class AgentError(Exception):
    """Base error for the agent SDK."""


class AgentStreamingError(AgentError):
    """Error raised when streaming fails."""
