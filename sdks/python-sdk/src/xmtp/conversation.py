"""Conversation models."""

from __future__ import annotations

from dataclasses import dataclass

from xmtp.errors import NotImplementedXmtpError


@dataclass(slots=True)
class Conversation:
    """Base conversation class."""

    id: str

    async def send(self, content: str) -> None:
        """Send a message in the conversation."""

        raise NotImplementedXmtpError('Conversation.send not implemented')


@dataclass(slots=True)
class Dm(Conversation):
    """Direct message conversation."""


@dataclass(slots=True)
class Group(Conversation):
    """Group conversation."""

    async def add_members(self, members: list[str]) -> None:
        """Add members to the group."""

        raise NotImplementedXmtpError('Group.add_members not implemented')

    async def remove_members(self, members: list[str]) -> None:
        """Remove members from the group."""

        raise NotImplementedXmtpError('Group.remove_members not implemented')

    async def members(self) -> list[str]:
        """Return group member addresses."""

        raise NotImplementedXmtpError('Group.members not implemented')

    async def add_admin(self, member: str) -> None:
        """Add an admin to the group."""

        raise NotImplementedXmtpError('Group.add_admin not implemented')

    async def remove_admin(self, member: str) -> None:
        """Remove an admin from the group."""

        raise NotImplementedXmtpError('Group.remove_admin not implemented')

    async def is_admin(self, member: str) -> bool:
        """Return True if member is an admin."""

        raise NotImplementedXmtpError('Group.is_admin not implemented')

    @property
    def name(self) -> str | None:
        """Group name."""

        raise NotImplementedXmtpError('Group.name not implemented')

    @property
    def description(self) -> str | None:
        """Group description."""

        raise NotImplementedXmtpError('Group.description not implemented')

    @property
    def image_url(self) -> str | None:
        """Group image URL."""

        raise NotImplementedXmtpError('Group.image_url not implemented')
